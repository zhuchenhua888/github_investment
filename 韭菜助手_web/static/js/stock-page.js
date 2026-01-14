// 股票页面JavaScript文件 - 移植自小程序的前端逻辑

let stockCharts = {};
let currentData = {};

document.addEventListener('DOMContentLoaded', function() {
    console.log('股票页面已加载');
    
    // 初始化页面
    loadStockData();
});

async function loadStockData() {
    showLoading();
    hideError();
    
    try {
        console.log('[Performance] Start loading stock data');
        const totalStartTime = performance.now();
        
        // 并行加载所有数据以提高效率
        console.time('Total API Requests');
        const [
            hushen300Response,
            bondYieldResponse,
            gdpResponse,
            stockMarketResponse,
            buffetResponse,
            fedPremiumResponse,
            moneySupplyResponse,
            cpiResponse,
            ppiResponse,
            marginResponse
        ] = await Promise.all([
            apiRequest('/api/data/hushen300'),
            apiRequest('/api/data/bond_yield'),
            apiRequest('/api/data/gdp'),
            apiRequest('/api/data/stock_market'),
            apiRequest('/api/data/buffet'),
            apiRequest('/api/data/fed_premium'),
            apiRequest('/api/data/money_supply'),
            apiRequest('/api/data/cpi'),
            apiRequest('/api/data/ppi'),
            apiRequest('/api/data/margin_account')
        ]);
        console.timeEnd('Total API Requests');
        
        // 存储数据
        currentData.hushen300Data = hushen300Response;
        currentData.bondYieldData = bondYieldResponse;
        currentData.gdpData = gdpResponse;
        currentData.stockMarketData = stockMarketResponse;
        currentData.buffetData = buffetResponse;
        currentData.fedPremiumData = fedPremiumResponse.ratio;
        currentData.riskPremiumData = fedPremiumResponse.diff;
        currentData.moneySupplyData = moneySupplyResponse;
        currentData.cpiData = cpiResponse;
        currentData.ppiData = ppiResponse;
        currentData.marginData = marginResponse;
        
        // 更新最后更新时间
        const now = new Date();
        const formattedDate = formatDate(now);
        document.getElementById('last-updated').textContent = formattedDate;
        
        // 渲染图表
        console.time('Render Charts');
        const page = window.PageAdapter && typeof window.PageAdapter.create === 'function'
          ? window.PageAdapter.create(currentData)
          : null;
          
        if (page && window.StockViews) {
          window.StockViews.renderHushen300Chart(page, { chartId: '#hushen300Chart', mode: 'ratio', leftName: '股债比' });
          window.StockViews.renderHushen300Chart(page, { chartId: '#riskPremiumChart', mode: 'diff', leftName: '风险溢价' });
          window.StockViews.renderMoneySupply(page);
          window.StockViews.renderBuffet(page);
          window.StockViews.renderCpiPpi(page);
          window.StockViews.renderMarginAccountInfo(page);
        }
        console.timeEnd('Render Charts');
        
        const totalEndTime = performance.now();
        console.log(`[Performance] Total load and render time: ${(totalEndTime - totalStartTime).toFixed(2)}ms`);
        
        // 显示数据概览
        updateDataOverview();
        
        hideLoading();
    } catch (error) {
        console.error('加载股票数据失败:', error);
        showError('数据加载失败: ' + error.message);
    }
}

function renderPlaceholderChart(chartId, title) {
    const chartDom = document.getElementById(chartId);
    if (!chartDom) {
        console.warn(`找不到图表容器: ${chartId}`);
        return;
    }
    
    const chart = echarts.init(chartDom);
    
    const option = {
        title: {
            text: title,
            left: 'center',
            top: 'center'
        },
        graphic: {
            type: 'text',
            left: 'center',
            top: 'middle',
            style: {
                text: '数据加载中...',
                fontSize: 16,
                textAlign: 'center',
                fill: '#666'
            }
        }
    };
    
    chart.setOption(option);
    stockCharts[chartId] = chart;
}

function updateDataOverview() {
    // 更新数据概览区域
    const data = currentData.hushen300Data || [];
    if (data.length > 0) {
        const latest = data[data.length - 1];
        document.getElementById('latest-index').textContent = latest.close || 'N/A';
        
        if (data.length >= 2) {
            const first = data[0];
            const last = data[data.length - 1];
            document.getElementById('date-range').textContent = 
                `${first.date || ''} 至 ${last.date || ''}`;
        }
        
        document.getElementById('data-overview').style.display = 'block';
    }
}

function showHelp(type) {
    if (window.StockHelp && typeof window.StockHelp.getHelpData === 'function') {
        const helpData = window.StockHelp.getHelpData(type);
        document.getElementById('help-title').innerHTML = helpData.title;
        document.getElementById('help-body').innerHTML = helpData.content;
    } else {
        console.error('StockHelp is not initialized');
        // 退退到原来的逻辑或者显示默认信息
        document.getElementById('help-title').innerHTML = '帮助信息';
        document.getElementById('help-body').innerHTML = '<p>暂无详细说明。</p>';
    }
    document.getElementById('help-modal').style.display = 'flex';
}

function closeHelp() {
    document.getElementById('help-modal').style.display = 'none';
}

// 页面卸载时清理图表
window.addEventListener('beforeunload', function() {
    Object.values(stockCharts).forEach(chart => {
        if (chart && typeof chart.dispose === 'function') {
            chart.dispose();
        }
    });
});
