from flask import Flask, render_template, jsonify, request
import os
import json
import requests
import time
from datetime import datetime, timedelta
from math import isnan

from api.stock_py import initialize_data_managers, update_all_data as stock_update_all_data
from api.stock_py.data.data_hushen300 import hushen300_manager
from api.stock_py.data.data_bond_yield import bond_yield_manager
from api.stock_py.data.data_gdp import china_gdp_manager
from api.stock_py.data.data_stock_market import china_stock_market_manager
from api.stock_py.data.data_cpi import china_cpi_manager
from api.stock_py.data.data_ppi import china_ppi_manager
from api.stock_py.data.data_money_supply import china_money_supply_manager
from api.stock_py.data.data_margin import margin_manager
from api.stock_py.data.data_listing_committee import listing_committee_manager

from api.stock_py.deal.deal_buffet import build_buffet_data
from api.stock_py.deal.deal_fed import calculate_fed_premium_both
from api.stock_py.deal.deal_cpi_ppi import build_cpi_data, build_ppi_data
from api.stock_py.deal.deal_money_supply import build_money_supply_data
from api.stock_py.deal.deal_margin_account_info import build_margin_account_info_data

from api.lof.lof_data_manager import lof_manager, get_lof_data, get_sorted_lof_data, get_lof_detail, initialize_lof_manager
from api.lof.get_lof_detail import fetch_lof_detail_data, process_lof_detail_data
from api.peizhai.peizhai_data_manager import peizhai_manager

app = Flask(__name__)

# 配置静态文件路径
app.static_folder = 'static'
app.template_folder = 'templates'

# 应用启动时初始化数据管理器
with app.app_context():
    initialize_data_managers()
    initialize_lof_manager()

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        duration = (time.time() - request.start_time) * 1000
        print(f"[Backend API] {request.path} took {duration:.2f}ms")
    return response

@app.route('/')
def index():
    """渲染首页模板"""
    return render_template('index.html')

@app.route('/stock')
def stock():
    return render_template('stock.html')

@app.route('/lof')
def lof():
    return render_template('lof.html')

@app.route('/lof_detail')
def lof_detail():
    fund_id = request.args.get('fund_id', '')
    fund_name = request.args.get('fund_name', f'LOF基金{fund_id}')
    return render_template('lof_detail.html', fund_id=fund_id, fund_name=fund_name)

@app.route('/etf')
def etf():
    return render_template('etf.html')

@app.route('/peizhai')
def peizhai():
    return render_template('peizhai.html')

@app.route('/listing_committee')
def listing_committee():
    return render_template('listing_committee.html')

@app.route('/about')
def about():
    return render_template('about.html')

# API接口 - 实现原来小程序中的数据处理逻辑
@app.route('/api/data/hushen300', methods=['GET'])
def get_hushen300_data():
    try:
        t1 = time.time()
        hushen300_manager.update_data()
        t2 = time.time()
        data = hushen300_manager.get_data()
        t3 = time.time()
        print(f"[Profiling] hushen300_manager.update_data took {(t2-t1)*1000:.2f}ms")
        print(f"[Profiling] hushen300_manager.get_data took {(t3-t2)*1000:.2f}ms")
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/bond_yield', methods=['GET'])
def get_bond_yield_data():
    try:
        t1 = time.time()
        bond_yield_manager.update_data()
        t2 = time.time()
        data = bond_yield_manager.get_data()
        t3 = time.time()
        print(f"[Profiling] bond_yield_manager.update_data took {(t2-t1)*1000:.2f}ms")
        print(f"[Profiling] bond_yield_manager.get_data took {(t3-t2)*1000:.2f}ms")
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/gdp', methods=['GET'])
def get_gdp_data():
    try:
        china_gdp_manager.update_data()
        data = china_gdp_manager.get_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/stock_market', methods=['GET'])
def get_stock_market_data():
    try:
        china_stock_market_manager.update_data()
        data = china_stock_market_manager.get_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/buffet', methods=['GET'])
def get_buffet_data():
    try:
        china_gdp_manager.update_data()
        china_stock_market_manager.update_data()
        gdp_data = china_gdp_manager.get_data()
        stock_market_data = china_stock_market_manager.get_data()
        buffet_data = build_buffet_data(gdp_data, stock_market_data)
        return jsonify(buffet_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/fed_premium', methods=['GET'])
def get_fed_premium_data():
    try:
        t1 = time.time()
        hushen300_data = hushen300_manager.get_data()
        bond_yield_data = bond_yield_manager.get_data()
        t2 = time.time()
        result = calculate_fed_premium_both(hushen300_data, bond_yield_data)
        t3 = time.time()
        print(f"[Profiling] fed_premium: get_data took {(t2-t1)*1000:.2f}ms")
        print(f"[Profiling] fed_premium: calculate took {(t3-t2)*1000:.2f}ms")
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/data/cpi', methods=['GET'])
def get_cpi_data():
    try:
        china_cpi_manager.update_data()
        data = build_cpi_data(china_cpi_manager.get_data())
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/data/ppi', methods=['GET'])
def get_ppi_data():
    try:
        china_ppi_manager.update_data()
        data = build_ppi_data(china_ppi_manager.get_data())
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/data/money_supply', methods=['GET'])
def get_money_supply_data():
    try:
        china_money_supply_manager.update_data()
        raw = china_money_supply_manager.get_data()
        data = build_money_supply_data(raw)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/api/data/margin_account', methods=['GET'])
def get_margin_account_data():
    try:
        margin_manager.update_data()
        hs = hushen300_manager.get_data()
        data = build_margin_account_info_data(margin_manager.get_data(), hs)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/listing_committee', methods=['GET'])
def get_listing_committee_data():
    try:
        # 如果当前没有数据，尝试从缓存加载
        if not listing_committee_manager.audit_data:
            listing_committee_manager.init_data()
            
        if listing_committee_manager.should_update():
            listing_committee_manager.fetch_from_api()
        return jsonify(listing_committee_manager.audit_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/update_all', methods=['POST'])
def update_all_data_route():
    try:
        stock_update_all_data()
        return jsonify({'message': '数据更新成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/lof', methods=['GET'])
def get_lof_data_api():
    try:
        # 使用LOF数据管理器获取数据
        data = get_lof_data()
        print(f'获取到LOF数据条数: {len(data)}')
        return jsonify(data)
    except Exception as e:
        print(f'获取LOF数据失败: {e}')
        import traceback
        traceback.print_exc()
        return jsonify([])

@app.route('/api/lof/detail', methods=['GET'])
def get_lof_detail_api():
    try:
        fund_id = request.args.get('fund_id')
        if not fund_id:
            return jsonify({'error': '缺少基金代码'}), 400
        
        raw_data = fetch_lof_detail_data(fund_id)
        processed_data = process_lof_detail_data(raw_data)
        return jsonify(processed_data)
    except Exception as e:
        print(f'获取LOF详情数据失败: {e}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/etf', methods=['GET'])
def get_etf_data():
    try:
        # 从东方财富或其他API获取ETF数据
        url = 'https://api.money.126.net/data/feed/etf/etfList'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # 处理数据格式以匹配前端需求
            processed_data = []
            for item in data.get('list', []):
                processed_data.append({
                    'fundCode': item.get('symbol', ''),
                    'fundName': item.get('name', ''),
                    'price': float(item.get('price', 0)),
                    'dailyChange': float(item.get('changePercent', 0)),
                    'ytdChange': float(item.get('ytdChange', 0)),
                    'index': item.get('index', '')
                })
            return jsonify(processed_data)
        else:
            # 如果API不可用，返回空数组
            return jsonify([])
    except Exception as e:
        print(f'获取ETF数据失败: {e}')
        return jsonify([])

@app.route('/api/data/peizhai', methods=['GET'])
def get_peizhai_data():
    try:
        data = peizhai_manager.fetch_from_api()
        return jsonify(data)
    except Exception as e:
        print(f'获取配债数据失败: {e}')
        return jsonify([])

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
