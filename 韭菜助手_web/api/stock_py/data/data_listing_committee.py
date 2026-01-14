import os
import json
import requests
import time
import re
from typing import List, Dict, Any
from .base_manager import BaseDataManager

class ListingCommitteeDataManager(BaseDataManager):
    def __init__(self):
        super().__init__()
        self.audit_data: List[Dict] = []
        self.cache_file = os.path.join(self.cache_dir, 'listing_committee_data.json')
        # 设置更新间隔为 12 小时，上市委信息更新频率较高
        self.update_interval = 3600 * 12

    def init_data(self):
        if os.path.exists(self.cache_file):
            try:
                self.last_update_time = os.path.getmtime(self.cache_file)
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cached = json.load(f)
                    self.audit_data = cached if isinstance(cached, list) else []
            except Exception:
                self.audit_data = []
        else:
            self.audit_data = []

    def _extract_jsonp(self, text: str) -> Dict[str, Any]:
        """提取 JSONP 中的 JSON 数据"""
        try:
            # 匹配 callback_name({...}) 格式
            match = re.search(r'^[^(]*\((.*)\)[^)]*$', text, re.DOTALL)
            if match:
                json_str = match.group(1)
                return json.loads(json_str)
            return json.loads(text)
        except Exception as e:
            print(f"Error extracting JSONP: {e}")
            return {}

    def _get_last_date(self, source: str) -> str:
        """获取指定市场的最后更新日期"""
        latest_date = "2025-01-01"  # 默认起始日期
        for group in self.audit_data:
            for item in group:
                if item.get('source') == source:
                    date = item.get('fileUpdateTime', '')
                    if date > latest_date:
                        latest_date = date
        return latest_date

    def fetch_from_api(self) -> List[Dict]:
        """从上交所和深交所接口获取上市委审核信息 (增量更新)"""
        try:
            # 1. 确保已加载现有数据
            if not self.audit_data:
                self.init_data()

            today = time.strftime('%Y-%m-%d')
            
            # 2. 获取上交所新数据
            sse_last_date = self._get_last_date('SSE')
            print(f"Fetching SSE data from {sse_last_date} to {today}")
            new_sse_items = self._fetch_sse_data_range(sse_last_date, today)
            
            # 3. 获取深交所新数据
            szse_last_date = self._get_last_date('SZSE')
            print(f"Fetching SZSE data from {szse_last_date} to {today}")
            new_szse_items = self._fetch_szse_data_range(szse_last_date, today)
            
            # 4. 合并并去重
            # 先将现有数据打平
            all_items = []
            for group in self.audit_data:
                all_items.extend(group)
            
            # 加入新数据
            all_items.extend(new_sse_items)
            all_items.extend(new_szse_items)
            
            # 去重 (使用 fileId)
            seen_ids = set()
            unique_items = []
            # 按时间倒序排，确保保留最新的（如果有重复 ID 但内容不同的话，虽然理论上 ID 唯一）
            all_items.sort(key=lambda x: x.get('fileUpdateTime', ''), reverse=True)
            for item in all_items:
                fid = item.get('fileId')
                if fid not in seen_ids:
                    unique_items.append(item)
                    seen_ids.add(fid)
            
            # 5. 重新按公司分组
            company_groups = {}
            for item in unique_items:
                name = item.get('companyName', '未知公司')
                if name not in company_groups:
                    company_groups[name] = []
                company_groups[name].append(item)
            
            # 6. 对每个分组内的条目按时间排序
            final_groups = []
            for name in company_groups:
                group = company_groups[name]
                group.sort(key=lambda x: x.get('fileUpdateTime', ''), reverse=True)
                final_groups.append(group)
            
            # 7. 对所有分组按其最新一条的时间排序
            final_groups.sort(key=lambda x: x[0].get('fileUpdateTime', ''), reverse=True)

            if final_groups:
                self.audit_data = final_groups
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump(self.audit_data, f, ensure_ascii=False, indent=4)
                self.last_update_time = time.time()
            
            return self.audit_data

        except Exception as e:
            print(f"Error fetching listing committee data: {e}")
            import traceback
            traceback.print_exc()
            return self.audit_data

    def _fetch_sse_data_range(self, start_date: str, end_date: str) -> List[Dict]:
        """获取上交所指定日期范围内的全量数据"""
        # 尝试使用带连字符的日期格式，与用户提供的 URL 一致
        begin_date = start_date
        finish_date = end_date
        
        all_processed_items = []
        headers = {
            'Referer': 'https://www.sse.com.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        audit_type_cache = {}
        page_no = 1
        
        while True:
            timestamp = int(time.time() * 1000)
            url = f"https://query.sse.com.cn/commonSoaQuery.do?jsonCallBack=jsonpCallback{timestamp}&isPagination=true&sqlId=GP_COMMITTEE_FILE_BATCH_SEARCH&pageHelp.pageSize=25&pageHelp.pageNo={page_no}&pageHelp.beginPage={page_no}&pageHelp.cacheSize=1&pageHelp.endPage={page_no}&fileTypeMap=I2010%2CI2011%2CI2021%2CI2020%2CS2010%2CS2020%2CT2010%2CT2020&companyName=&searchDateBegin={begin_date}&searchDateEnd={finish_date}&_={timestamp}"
            
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    break

                data = self._extract_jsonp(resp.text)
                if not isinstance(data, dict):
                    break
                
                # 处理 result 可能为 null 的情况
                groups = data.get('result') or []
                if not groups:
                    # 如果第一页就没数据，或者报错，尝试切换日期格式
                    if page_no == 1 and begin_date.find('-') != -1:
                        begin_date = begin_date.replace('-', '')
                        finish_date = finish_date.replace('-', '')
                        continue
                    break
                
                new_items_count = 0
                for group in groups:
                    if not isinstance(group, list):
                        group = [group]
                    
                    for item in group:
                        fid = item.get('fileId')
                        if not fid: continue
                        
                        # 获取审核类型详情
                        audit_type_str = audit_type_cache.get(fid)
                        if not audit_type_str:
                            ts = int(time.time() * 1000)
                            url2 = f"https://query.sse.com.cn/sseQuery/commonSoaQuery.do?&jsonCallBack=jsonpCallback{ts}&sqlId=GP_COMMITTEE_ISSUER_ORDER&fileId={fid}&_={ts}"
                            try:
                                resp2 = requests.get(url2, headers=headers, timeout=5)
                                if resp2.status_code == 200:
                                    data2 = self._extract_jsonp(resp2.text)
                                    details = data2.get('result', [])
                                    if details:
                                        audit_type_val = str(details[0].get('auditType', ''))
                                        if audit_type_val == "1": audit_type_str = "主板IPO"
                                        elif audit_type_val == "3": audit_type_str = "再融资"
                                        else: audit_type_str = "其他"
                                    audit_type_cache[fid] = audit_type_str
                                time.sleep(0.05)
                            except: audit_type_str = "未知"

                        raw_time = item.get('fileUpdateTime', '')
                        formatted_time = f"{raw_time[:4]}-{raw_time[4:6]}-{raw_time[6:8]}" if len(raw_time) >= 8 else ""

                        all_processed_items.append({
                            'companyName': item.get('companyName'),
                            'auditType': audit_type_str or "未知",
                            'fileTitle': item.get('fileTitle'),
                            'fileUpdateTime': formatted_time,
                            'fileId': fid,
                            'source': 'SSE'
                        })
                        new_items_count += 1
                
                # 如果当前页没有新数据，或者数据量小于 pageSize，说明拿完了
                if new_items_count == 0:
                    break
                
                page_no += 1
                time.sleep(0.2) # 稍微慢一点，防止被封
            except Exception as e:
                print(f"SSE fetch range error at page {page_no}: {e}")
                break
                
        return all_processed_items

    def _fetch_szse_data_range(self, start_date: str, end_date: str) -> List[Dict]:
        """获取深交所指定日期范围内的全量数据"""
        all_processed_items = []
        headers = {
            'Referer': 'https://listing.szse.cn/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        page_index = 0
        page_size = 20 # 增加每页数量减少请求次数
        
        while True:
            url = f"https://listing.szse.cn/api/ras/ANNCNotice/queryMeetingNotice?pageIndex={page_index}&pageSize={page_size}&catalog=5&keywords=&disclosedStartDate={start_date}&disclosedEndDate={end_date}&random={time.time()}"
            
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    break

                data = resp.json()
                items = data.get('data', [])
                if not items:
                    break
                
                for item in items:
                    dfid = item.get('dfid')
                    if not dfid: continue
                    
                    # 获取详情
                    url2 = f"https://listing.szse.cn/api/ras/ANNCNotice/queryMeetingNoticeDetail?id={dfid}&random={time.time()}"
                    try:
                        resp2 = requests.get(url2, headers=headers, timeout=5)
                        if resp2.status_code == 200:
                            detail_data = resp2.json()
                            detail = detail_data.get('data', {})
                            projects = detail.get('projects', [])
                            disclosures = detail.get('subInfoDisclosureList', [])
                            
                            for proj in projects:
                                company_name = proj.get('cmpnm') or proj.get('cmpsnm')
                                biz_type_val = proj.get('biztype')
                                audit_type_str = "主板IPO" if biz_type_val == 1 else ("再融资" if biz_type_val == 2 else "其他")
                                
                                # 1. 添加主公告
                                all_processed_items.append({
                                    'companyName': company_name,
                                    'auditType': audit_type_str,
                                    'fileTitle': detail.get('dftitle') or item.get('dftitle'),
                                    'fileUpdateTime': detail.get('ddt') or item.get('ddt'),
                                    'fileId': str(dfid),
                                    'source': 'SZSE'
                                })
                                
                                # 2. 添加子公告
                                for disc in disclosures:
                                    sub_dfid = disc.get('dfid')
                                    if not disc.get('dftitle') or not sub_dfid: continue
                                    all_processed_items.append({
                                        'companyName': company_name,
                                        'auditType': audit_type_str,
                                        'fileTitle': disc.get('dftitle'),
                                        'fileUpdateTime': disc.get('ddt') or detail.get('ddt'),
                                        'fileId': str(sub_dfid),
                                        'source': 'SZSE'
                                    })
                        time.sleep(0.05)
                    except Exception as e:
                        print(f"SZSE detail fetch error for {dfid}: {e}")

                total_page = data.get('totalPage', 0)
                if page_index + 1 >= total_page:
                    break
                    
                page_index += 1
                time.sleep(0.2)
            except Exception as e:
                print(f"SZSE fetch range error at page {page_index}: {e}")
                break
                
        return all_processed_items

listing_committee_manager = ListingCommitteeDataManager()
