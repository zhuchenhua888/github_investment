from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import sys

def get_jisilu_cbnew_data():
    # 配置Chrome浏览器选项
    options = webdriver.ChromeOptions()
    
    # 添加更全面的浏览器选项
    options.add_argument("--headless=new")  # 启用无头模式，减少UI问题
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")  # 指定窗口大小
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-dev-shm-usage")  # 解决共享内存问题
    options.add_argument("--remote-debugging-port=9222")  # 避免端口冲突
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    
    # 尝试不同的初始化方式
    try:
        # 显式指定ChromeDriver路径
        driver_path = ChromeDriverManager().install()
        print(f"ChromeDriver路径: {driver_path}")
        
        driver = webdriver.Chrome(
            service=Service(driver_path),
            options=options
        )
    except Exception as e:
        print(f"初始化浏览器失败: {e}")
        # 尝试备选方案 - 手动指定驱动（需要用户根据实际路径修改）
        try:
            # 请将下面的路径替换为你实际的ChromeDriver路径
            manual_driver_path = "C:/chromedriver.exe"  # Windows示例
            # manual_driver_path = "/usr/local/bin/chromedriver"  # Linux/Mac示例
            driver = webdriver.Chrome(
                service=Service(manual_driver_path),
                options=options
            )
        except Exception as e2:
            print(f"手动指定驱动也失败: {e2}")
            return None
    
    try:
        # 目标URL
        url = "https://www.jisilu.cn/data/cbnew/#pre"
        
        # 打开页面
        driver.get(url)
        
        # 增加延迟时间，确保页面加载
        time.sleep(random.uniform(3, 5))
        
        # 等待表格加载完成（延长等待时间到15秒）
        wait = WebDriverWait(driver, 15)
        table = wait.until(
            EC.presence_of_element_located((By.ID, "pre"))
        )
        
        # 滚动到表格位置
        driver.execute_script("arguments[0].scrollIntoView();", table)
        time.sleep(2)
        
        # 获取页面源码并解析
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', {'id': 'pre'})
        
        if not table:
            print("未找到待发转债表格")
            return None
        
        # 提取表头
        headers = []
        th_elements = table.find_all('th')
        for th in th_elements:
            headers.append(th.text.strip())
        
        # 提取表格数据
        data = []
        tr_elements = table.find_all('tr')[1:]  # 跳过表头行
        for tr in tr_elements:
            row = []
            td_elements = tr.find_all('td')
            for td in td_elements:
                row.append(td.text.strip())
            if row:  # 确保行不为空
                data.append(row)
        
        # 创建DataFrame
        df = pd.DataFrame(data, columns=headers)
        
        # 保存为CSV文件
        filename = f"jisilu_cbnew_{time.strftime('%Y%m%d')}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"数据已成功保存到 {filename}")
        
        return df
    
    except Exception as e:
        print(f"获取数据时出错: {str(e)}")
        # 输出页面源码用于调试
        try:
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("已保存页面源码到debug_page_source.html用于调试")
        except:
            pass
    finally:
        # 确保浏览器关闭
        try:
            driver.quit()
        except:
            pass
    
    return None

if __name__ == "__main__":
    # 确保中文显示正常
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
    
    # 添加随机延迟
    time.sleep(random.uniform(1, 3))
    df = get_jisilu_cbnew_data()
    
    if df is not None:
        print("\n获取的待发转债数据预览:")
        print(df.head())
    