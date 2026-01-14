import os
import requests
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import time
from api.stock_py.data.base_manager import BaseDataManager


class LOFDataManager(BaseDataManager):
    """LOF基金数据管理类 - 移植自小程序的lof.js逻辑"""
    
    def __init__(self):
        super().__init__()
        self.lof_data = []
        self.cache_file = None
        self.current_api = 1
        self.sort_field = 'discount_rt'  # 默认排序字段
        self.sort_order = 'desc'  # 默认排序方式
    
    def init_data(self):
        """初始化数据：不使用缓存"""
        self.lof_data = []
    
    def fetch_from_api(self) -> List[Dict]:
        """从API获取LOF数据（仅使用真实接口，不返回示例数据）"""
        try:
            ts = int(time.time() * 1000)
            urls = [
                f'https://www.jisilu.cn/data/qdii/qdii_list/E?___jsl=LST___t={ts}&only_lof=y&rp=22',
                f'https://www.jisilu.cn/data/qdii/qdii_list/C?___jsl=LST___t={ts}',
                f'https://www.jisilu.cn/data/lof/index_lof_list/?___jsl=LST___t={ts}&only_owned=&rp=25'
            ]
            session = requests.Session()
            cookie = os.environ.get('JISILU_COOKIE', '').strip()
            base_headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.jisilu.cn/data/qdii/',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://www.jisilu.cn',
                'Connection': 'keep-alive'
            }
            if cookie:
                base_headers['Cookie'] = cookie

            all_rows = []
            for url in urls:
                try:
                    # 对于 index_lof_list 接口，设置特定的 Referer
                    headers = base_headers.copy()
                    if 'index_lof_list' in url:
                        headers['Referer'] = 'https://www.jisilu.cn/data/lof/'
                    
                    response = session.get(url, headers=headers, timeout=15)
                    print(f"请求URL: {url}, 状态码: {response.status_code}")
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if isinstance(data, dict) and 'rows' in data:
                                if 'index_lof_list' in url:
                                    # 针对国投白银LOF(161226)进行过滤
                                    silver_rows = [row for row in data['rows'] if row.get('id') == '161226']
                                    all_rows.extend(silver_rows)
                                    print(f"从URL {url} 提取到 {len(silver_rows)} 条(161226)数据")
                                else:
                                    all_rows.extend(data['rows'])
                                    print(f"从URL {url} 获取到 {len(data['rows'])} 条数据")
                            else:
                                print(f"响应无rows或格式异常，尝试代理获取")
                        except ValueError:
                            print("直接JSON解析失败，尝试代理获取")
                    else:
                        print(f"请求失败，状态码: {response.status_code}，尝试代理获取")
                except Exception as e:
                    print(f"直接获取异常: {e}，尝试代理获取")

                # 代理回退：r.jina.ai
                if not all_rows or ('index_lof_list' in url and not any(r.get('id') == '161226' for r in all_rows)):
                    try:
                        if 'index_lof_list' in url:
                            proxy_url = f'https://r.jina.ai/https://www.jisilu.cn/data/lof/index_lof_list/?only_owned=&rp=25'
                        else:
                            proxy_url = f'https://r.jina.ai/http://www.jisilu.cn/data/qdii/qdii_list/{ "E?only_lof=y&rp=22" if "qdii_list/E" in url else "C"}'
                        
                        proxy_resp = session.get(proxy_url, headers=base_headers, timeout=15)
                        if proxy_resp.status_code == 200:
                            txt = proxy_resp.text
                            try:
                                data2 = json.loads(txt)
                                if isinstance(data2, dict) and 'rows' in data2:
                                    if 'index_lof_list' in url:
                                        silver_rows = [row for row in data2['rows'] if row.get('id') == '161226']
                                        all_rows.extend(silver_rows)
                                        print(f"代理从 index_lof_list 提取到 {len(silver_rows)} 条(161226)数据")
                                    else:
                                        all_rows.extend(data2['rows'])
                                        print(f"代理获取到 {len(data2['rows'])} 条数据")
                            except Exception as je:
                                print(f"代理内容非JSON：{je}")
                    except Exception as pe:
                        print(f"代理获取失败：{pe}")

            processed_data = []
            for item in all_rows:
                cell = item.get('cell', {})
                raw_discount = cell.get('discount_rt', '-')
                if isinstance(raw_discount, (int, float)):
                    discount_rt_val = float(raw_discount)
                else:
                    s = str(raw_discount).strip()
                    if s in ('-', ''):
                        discount_rt_val = '-'
                    else:
                        s = s.replace('%', '').replace(',', '')
                        try:
                            discount_rt_val = float(s)
                        except Exception:
                            discount_rt_val = '-'

                amount_incr = cell.get('amount_incr', '0')
                if amount_incr and not (isinstance(amount_incr, str) and amount_incr == '-'):
                    try:
                        num_amount_incr = float(amount_incr)
                        formatted_amount_incr = ('+' if num_amount_incr >= 0 else '-') + str(abs(num_amount_incr))
                    except (ValueError, TypeError):
                        formatted_amount_incr = '+0'
                else:
                    formatted_amount_incr = '+0'

                processed_data.append({
                    'fund_id': cell.get('fund_id', ''),
                    'fund_nm': cell.get('fund_nm', ''),
                    'price': float(cell.get('price', 0)) if cell.get('price') else 0,
                    'discount_rt': discount_rt_val,
                    'apply_status': cell.get('apply_status', 'N'),
                    'amount': cell.get('amount', ''),
                    'amount_incr': formatted_amount_incr
                })

            print(f"最终LOF记录数：{len(processed_data)}")
            return processed_data

        except Exception as e:
            print(f"获取LOF数据失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def update_data(self):
        """更新LOF数据"""
        try:
            new_data = self.fetch_from_api()
            if new_data:
                sorted_data = sorted(
                    new_data,
                    key=lambda x: float('-inf') if x['discount_rt'] == '-' else x['discount_rt'],
                    reverse=True
                )
                self.lof_data = sorted_data
        except Exception as e:
            print(f"更新LOF数据失败: {e}")
    
    def get_data(self) -> List[Dict]:
        """获取LOF数据"""
        return self.lof_data
    
    def sort_data(self, field: str = None, order: str = None) -> List[Dict]:
        """排序数据"""
        if field is None:
            field = self.sort_field
        if order is None:
            order = self.sort_order
        
        sorted_data = sorted(self.lof_data, key=lambda x: self._get_sort_value(x, field), 
                            reverse=(order == 'desc'))
        
        # 更新排序设置
        self.sort_field = field
        self.sort_order = order
        
        return sorted_data
    
    def _get_sort_value(self, item: Dict, field: str):
        """获取用于排序的值"""
        value = item.get(field)
        
        if field in ['price', 'discount_rt', 'amount']:
            if field == 'discount_rt' and value == '-':
                return float('-inf')  # 将'-'排到最后
            try:
                return float(value) if value is not None else 0
            except (ValueError, TypeError):
                return 0
        else:
            return value if value is not None else ''
    
    def get_lof_detail(self, fund_id: str) -> Optional[Dict]:
        """获取特定LOF基金的详细信息"""
        for item in self.lof_data:
            if item.get('fund_id') == fund_id:
                return item
        return None


# 创建全局LOF数据管理实例
lof_manager = LOFDataManager()


def initialize_lof_manager():
    """初始化LOF数据管理器"""
    lof_manager.init_data()


def get_lof_data() -> List[Dict]:
    """获取LOF数据的便捷函数"""
    live_data = lof_manager.fetch_from_api()
    if not live_data:
        return []
    sorted_data = lof_manager.sort_data('discount_rt', 'desc') if lof_manager.lof_data else sorted(
        live_data,
        key=lambda x: float('-inf') if x['discount_rt'] == '-' else x['discount_rt'],
        reverse=True
    )
    lof_manager.lof_data = sorted_data
    return sorted_data


def get_sorted_lof_data(field: str = None, order: str = None) -> List[Dict]:
    """获取排序后的LOF数据的便捷函数"""
    return lof_manager.sort_data(field, order)


def get_lof_detail(fund_id: str) -> Optional[Dict]:
    """获取特定LOF基金详细信息的便捷函数"""
    return lof_manager.get_lof_detail(fund_id)
