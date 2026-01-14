window.StockViews = window.StockViews || {};
window.StockViews.renderHushen300Chart = function(page, opts) {
  if (!page || !page.data) return;
  const mode = opts && opts.mode ? opts.mode : 'ratio';
  const chartId = opts && opts.chartId ? opts.chartId : '#hushen300Chart';
  const leftName = opts && opts.leftName ? opts.leftName : 'FED溢价';
  const valueField = mode === 'diff' ? 'riskPremium' : 'fedPremium';

  const hushen300Data = page._hushen300Data || page.data.hushen300Data || [];
  const premiumData = (mode === 'diff'
    ? (page._riskPremiumData || page.data.riskPremiumData)
    : (page._fedPremiumData || page.data.fedPremiumData)) || null;
  if (!Array.isArray(hushen300Data) || hushen300Data.length === 0 || !premiumData) return;

  const label = `render_fed_${mode}_${chartId}`;
  console.time(label);
  const categories = [];
  const hushen300SeriesData = [];
  const premiumMap = new Map();
  const pegSeriesData = [];

  const tenYearsAgo = new Date();
  tenYearsAgo.setFullYear(tenYearsAgo.getFullYear() - 10);
  function isInLastTenYears(dateStr) {
    if (!dateStr) return false;
    const d = new Date(dateStr.replace(/(\d{4})-(\d{2})-(\d{2})/, '$1-$2-$3'));
    return d >= tenYearsAgo;
  }

  if (premiumData && premiumData.data) {
    premiumData.data.forEach(item => { if (item.date) premiumMap.set(item.date, item[valueField]); });
  }

  hushen300Data.forEach(item => {
    const date = item.tradeDate || item.date || '';
    const value = parseFloat(item.close || 0);
    const peg = parseFloat(item.peg || 0);
    if (date && !isNaN(value) && isInLastTenYears(date)) {
      categories.push(date);
      hushen300SeriesData.push(value);
      pegSeriesData.push(peg);
    }
  });

  const premiumSeries = categories.map(d => (premiumMap.has(d) ? premiumMap.get(d) : null));

  const dom = document.getElementById(chartId.replace('#', ''));
  if (!dom || !window.echarts) return;
  const chart = echarts.init(dom);
    const seriesData = [
      { name: '沪深300指数', type: 'line', yAxisIndex: 0, data: hushen300SeriesData, smooth: true, lineStyle: { width: 2, color: 'lightgrey' }, symbol: 'circle', showSymbol: false },
      { name: leftName, type: 'line', yAxisIndex: 1, data: premiumSeries, smooth: true, lineStyle: { width: 2, color: '#4751A5' }, symbol: 'circle', showSymbol: false }
    ];
    if (premiumData.mean !== undefined && premiumData.std !== undefined) {
      const mean_val = premiumData.mean;
      const std_val = premiumData.std;
      seriesData.push({ name: '均值+2σ', type: 'line', yAxisIndex: 1, data: Array(categories.length).fill(mean_val + 2 * std_val), lineStyle: { type: 'dashed', color: 'red', opacity: 0.7 }, symbol: 'none', showSymbol: false });
      seriesData.push({ name: '均值+1σ', type: 'line', yAxisIndex: 1, data: Array(categories.length).fill(mean_val + std_val), lineStyle: { type: 'dashed', color: 'orange', opacity: 0.7 }, symbol: 'none', showSymbol: false });
      seriesData.push({ name: `均值(${mean_val.toFixed(2)})`, type: 'line', yAxisIndex: 1, data: Array(categories.length).fill(mean_val), lineStyle: { type: 'dashed', color: 'yellow', opacity: 0.7 }, symbol: 'none', showSymbol: false });
      seriesData.push({ name: '均值-1σ', type: 'line', yAxisIndex: 1, data: Array(categories.length).fill(mean_val - std_val), lineStyle: { type: 'dashed', color: 'blue', opacity: 0.7 }, symbol: 'none', showSymbol: false });
      seriesData.push({ name: '均值-2σ', type: 'line', yAxisIndex: 1, data: Array(categories.length).fill(mean_val - 2 * std_val), lineStyle: { type: 'dashed', color: 'green', opacity: 0.7 }, symbol: 'none', showSymbol: false });
    }

    const option = {
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#d1d9e0',
        borderWidth: 1,
        borderRadius: 8,
        padding: [4, 4],
        textStyle: { fontSize: 13, lineHeight: 20, color: '#333333' },
        formatter: function(params) {
          const date = params[0].axisValue;
          const closePrice = params[0].data;
          const premiumVal = params[1] ? params[1].data : 'N/A';
          const index = params[0].dataIndex;
          const pegValue = pegSeriesData[index] || 0;
          const f2 = v => (typeof v === 'number' ? v.toFixed(2) : v);
          const formattedClosePrice = f2(closePrice);
          const formattedPegValue = f2(pegValue);
          const formattedPremium = (typeof premiumVal === 'number'
            ? (mode === 'diff' ? `${(premiumVal * 100).toFixed(2)}%` : f2(premiumVal))
            : premiumVal);
          let intervalText = '数据不可用';
          if (typeof premiumVal === 'number' && premiumData && premiumData.std) {
            const mean = premiumData.mean;
            const std = premiumData.std;
            if (premiumVal > mean + 2 * std) intervalText = '💚 估值极低';
            else if (premiumVal > mean + std) intervalText = '🔻 估值偏低';
            else if (premiumVal > mean) intervalText = '➖ 估值中等偏低';
            else if (premiumVal > mean - std) intervalText = '➖ 估值中等偏高';
            else if (premiumVal > mean - 2 * std) intervalText = '🔺 估值偏高';
            else intervalText = '⚡ 估值极高';
          }
          return `📅 ${date}\n<br/>📊 市场数据\n<br/>  沪深300指数：${formattedClosePrice}\n<br/>  市盈率(P/E)：${formattedPegValue}\n<br/>💰 估值指标\n<br/>  ${leftName}：${formattedPremium}\n<br/>  ${intervalText}`;
        }
      },
      grid: { left: '2%', right: '5%', top: '25%', bottom: '2%', containLabel: true },
      xAxis: [{ type: 'category', data: categories, axisLine: { show: false }, axisTick: { show: false } }],
      yAxis: [
        { type: 'value', position: 'left', show: true, axisLine: { show: false }, axisLabel: { show: true }, splitLine: { show: true, lineStyle: { type: 'dashed', color: '#e0e0e0' } }, scale: true },
        { type: 'value', position: 'right', show: true, axisLine: { show: false }, axisLabel: { show: true }, splitLine: { show: false }, scale: true }
      ],
      series: seriesData,
      legend: { top: '1%', left: 'center' },
      animation: false
    };
  chart.setOption(option);
  console.log(label, { points: categories.length });
  console.timeEnd(label);
  return chart;
};
