window.StockViews = window.StockViews || {};
window.StockViews.renderBuffet = function(page) {
  if (!page || !page.data) return;
  const data = page._buffetData || page.data.buffetData || [];
  const hushen300Data = page._hushen300Data || page.data.hushen300Data || [];
  if (!Array.isArray(data) || data.length === 0) {
    console.warn('buffetData 为空或未提供，跳过渲染');
    return;
  }

  const label = 'render_buffet';
  console.time(label);

  const categories = [];
  const ratio = [];
  const hushen = [];

  function monthFromQuarterLabel(label) {
    const m = String(label).match(/(\d{4}).*?第(\d)季度/);
    if (!m) return null;
    const y = m[1];
    const q = parseInt(m[2], 10);
    const monthMap = { 1: '03', 2: '06', 3: '09', 4: '12' };
    return `${y}-${monthMap[q]}`;
  }

  function getMonthEndClose(ym) {
    if (!ym || !Array.isArray(hushen300Data)) return null;
    let last = null;
    hushen300Data.forEach(item => {
      const d = item.date || item.tradeDate || '';
      if (typeof d === 'string' && d.startsWith(ym)) {
        const v = parseFloat(item.close || item.value || 0);
        if (isFinite(v)) last = v; // 逐步更新，最后一个即该月最后一个交易日
      }
    });
    return last;
  }

  data.forEach(item => {
    const date = item.date || '';
    const r = parseFloat(item.ratio ?? item.buffetRatio ?? item.marketCapToGDP);
    if (date) {
      categories.push(date);
      ratio.push(isFinite(r) ? r : null);
      const ym = monthFromQuarterLabel(date);
      const hs = ym ? getMonthEndClose(ym) : null;
      hushen.push(typeof hs === 'number' ? hs : null);
    }
  });

  const dom = document.getElementById('buffetChart');
  if (!dom || !window.echarts) return;
  const chart = echarts.init(dom);
  const option = {
      //title: { text: '巴菲特指标：A股总市值/中国国内GDP 与 沪深300', left: 'center', top: '2%', textStyle: { fontSize: 14, color: '#686868' } },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#d1d9e0', borderWidth: 1, borderRadius: 8, padding: [4,4],
        textStyle: { fontSize: 13, color: '#333' },
        formatter: params => {
          const date = params[0]?.axisValue || '';
          const rv = params.find(p => p.seriesName === '总市值/GDP')?.data;
          const hs = params.find(p => p.seriesName === '沪深300指数')?.data;
          const f = v => (typeof v === 'number' ? v.toFixed(2) : 'N/A');
          return `📅 ${date}\n<br/>` +
                 `总市值/GDP：${f(rv)}\n<br/>` +
                 `沪深300指数：${f(hs)}<br/>`;
        }
      },
      grid: { left: '5%', right: '5%', top: '12%', bottom: '2%', containLabel: true },
      xAxis: [{ type: 'category', data: categories, axisLine: { show: false }, axisTick: { show: false } }],
      yAxis: [
        { type: 'value', position: 'left', scale: true, axisLine: { show: false }, splitLine: { show: true, lineStyle: { type: 'dashed', color: '#e0e0e0' } }},
        { type: 'value', position: 'right', scale: true, axisLine: { show: false }, splitLine: { show: false }}
      ],
      legend: { top: '2%', left: 'center' },
      series: [
        { name: '总市值/GDP', type: 'line', yAxisIndex: 0, data: ratio, lineStyle: { width: 2, color: '#4751A5' }, symbol: 'circle', showSymbol: false },
        { name: '沪深300指数', type: 'line', yAxisIndex: 1, data: hushen, lineStyle: { width: 2, color: 'grey' }, symbol: 'circle', showSymbol: true }
      ],
      animation: false
    };
  chart.setOption(option);
  console.log(label, { points: categories.length });
  console.timeEnd(label);
  return chart;
}
