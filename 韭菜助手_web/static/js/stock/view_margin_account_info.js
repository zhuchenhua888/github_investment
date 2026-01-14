window.StockViews = window.StockViews || {};
window.StockViews.renderMarginAccountInfo = function(page) {
  if (!page || !page.data) return;
  const rows = page._marginAccountInfoData || page.data.marginAccountInfoData || null;
  if (!rows) return;
  let hasData = false;
  if (Array.isArray(rows)) {
    hasData = rows.length > 0;
  } else if (typeof rows === 'object') {
    hasData = Array.isArray(rows.categories) && rows.categories.length > 0;
  }
  if (!hasData) return;

  const label = 'render_margin_account_info';
  console.time(label);
  const dom = document.getElementById('marginAccountInfoChart');
  if (!dom || !window.echarts) return;
  const chart = echarts.init(dom);
  let categories = [];
  let leftSeries = [];
  let rightSeries = [];
  const d = rows;
  if (d && typeof d === 'object' && Array.isArray(d.categories) && Array.isArray(d.leftSeries) && Array.isArray(d.rightSeries)) {
    categories = d.categories;
    leftSeries = d.leftSeries;
    rightSeries = d.rightSeries;
  } else {
    rows.forEach(it => {
      const dt = it.date || it.tradeDate || it.month || '';
      const leftVal = typeof it.margin_balance === 'number' ? it.margin_balance : it.fin_balance;
      const rightVal = typeof it.hs300 === 'number' ? it.hs300 : it.close;
      if (dt) {
        categories.push(dt);
        leftSeries.push(typeof leftVal === 'number' ? leftVal : null);
        rightSeries.push(typeof rightVal === 'number' ? rightVal : null);
      }
    });
  }
  const option = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.95)',
        borderColor: '#d1d9e0',
        borderWidth: 1,
        borderRadius: 8,
        padding: [4,4],
        textStyle: { fontSize: 13, color: '#333' },
        formatter: params => {
          const date = params[0]?.axisValue || '';
          const left = params.find(p => p.seriesName === '融资-融券余额')?.data;
          const right = params.find(p => p.seriesName === '沪深300指数')?.data;
          const f = v => (typeof v === 'number' ? v.toFixed(2) : 'N/A');
          return `📅 ${date}\n<br/>` +
                 `融资-融券余额：${f(left)}\n<br/>` +
                 `沪深300指数：${f(right)}`;
        }
      },
      grid: { left: '5%', right: '5%', top: '12%', bottom: '2%', containLabel: true },
      xAxis: [{ type: 'category', data: categories, axisLine: { show: false }, axisTick: { show: false } }],
      yAxis: [
        { type: 'value', position: 'left', scale: true, axisLine: { show: false }, splitLine: { show: true, lineStyle: { type: 'dashed', color: '#e0e0e0' } } },
        { type: 'value', position: 'right', scale: true, axisLine: { show: false }, splitLine: { show: false } }
      ],
      legend: { top: '2%', left: 'center' },
      series: [
        { name: '融资-融券余额', type: 'line', yAxisIndex: 0, data: leftSeries, lineStyle: { width: 2, color: '#4751A5' }, symbol: 'circle', showSymbol: false },
        { name: '沪深300指数', type: 'line', yAxisIndex: 1, data: rightSeries, lineStyle: { width: 2, color: 'grey' }, symbol: 'circle', showSymbol: true }
      ],
      animation: false
    };
    chart.setOption(option);
  console.log(label, { points: categories.length });
  console.timeEnd(label);
  return chart;
}
