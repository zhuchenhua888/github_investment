window.StockViews = window.StockViews || {};
window.StockViews.renderMoneySupply = function(page) {
  if (!page || !page.data) return;
  let data = page._moneySupplyData || page.data.moneySupplyData || [];
  if (!Array.isArray(data)) {
    const obj = data || {};
    const dates = obj.dates || obj.months;
    const m1Arr = obj.m1YoY || obj.m1_yoy;
    const m2Arr = obj.m2YoY || obj.m2_yoy;
    if (Array.isArray(dates) && Array.isArray(m1Arr) && Array.isArray(m2Arr)) {
      data = dates.map((d, i) => ({
        month: d,
        m1_yoy: m1Arr[i],
        m2_yoy: m2Arr[i],
        diff: (typeof m1Arr[i] === 'number' && typeof m2Arr[i] === 'number') ? (m1Arr[i] - m2Arr[i]) : null
      }));
    } else {
      data = [];
    }
  }
  if (!Array.isArray(data) || data.length === 0) return;
  const label = 'render_money_supply';
  console.time(label);

  const categories = [];
  const m1 = [];
  const m2 = [];
  const diff = [];

  data.forEach(item => {
    const date = item.month || item.date || item.tradeDate || '';
    const m1y = parseFloat(item.m1YoY ?? item.M1YoY ?? item.m1_yoy);
    const m2y = parseFloat(item.m2YoY ?? item.M2YoY ?? item.m2_yoy);
    const d = typeof item.m1m2YoY !== 'undefined' ? parseFloat(item.m1m2YoY) : (isFinite(m1y) && isFinite(m2y) ? (m1y - m2y) : NaN);
    if (date) {
      categories.push(date);
      m1.push(isFinite(m1y) ? m1y : null);
      m2.push(isFinite(m2y) ? m2y : null);
      diff.push(isFinite(d) ? d : null);
    }
  });

  const dom = document.getElementById('moneySupplyChart');
  if (!dom || !window.echarts) return;
  const chart = echarts.init(dom);
  // 左右 Y 轴零点对齐（对称范围设置）
    const numsLeft = [...m1, ...m2].filter(v => typeof v === 'number');
    const maxAbsLeft = numsLeft.length ? Math.max(...numsLeft.map(v => Math.abs(v))) : 10;
    const numsRight = diff.filter(v => typeof v === 'number');
    const maxAbsRight = numsRight.length ? Math.max(...numsRight.map(v => Math.abs(v))) : 10;
    const pad = 1;
    const option = {
      //title: { text: '中国货币供应：M1/M2同比与差值', left: 'center', top: '2%', textStyle: { fontSize: 14, color: '#686868' } },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.95)',
        borderColor: '#d1d9e0', borderWidth: 1, borderRadius: 8, padding: [4,4],
        textStyle: { fontSize: 13, color: '#333' },
        formatter: params => {
          const date = params[0]?.axisValue || '';
          const m1v = params.find(p => p.seriesName === 'M1同比')?.data;
          const m2v = params.find(p => p.seriesName === 'M2同比')?.data;
          const dv = params.find(p => p.seriesName === 'M1-M2同比(右轴)')?.data;
          const f = v => (typeof v === 'number' ? `${v.toFixed(2)}%` : 'N/A');
          return `📅 ${date}\n<br/>` +
                 `M1同比：${f(m1v)}\n<br/>` +
                 `M2同比：${f(m2v)}\n<br/>` +
                 `M1-M2同比(右轴)：${f(dv)}`;
        }
      },
      grid: { left: '5%', right: '5%', top: '12%', bottom: '2%', containLabel: true },
      xAxis: [{ type: 'category', data: categories, axisLine: { show: false }, axisTick: { show: false } }],
      yAxis: [
        { type: 'value', position: 'left', axisLine: { show: false }, axisLabel: { formatter: value => `${value}%` }, splitLine: { show: true, lineStyle: { type: 'dashed', color: '#e0e0e0' } }, min: -(maxAbsLeft + pad), max: (maxAbsLeft + pad) },
        { type: 'value', position: 'right', axisLine: { show: false }, axisLabel: { formatter: value => `${value}%` }, splitLine: { show: false }, min: -(maxAbsRight + pad), max: (maxAbsRight + pad) }
      ],
      legend: { top: '2%', left: 'center' },
      series: [
        { name: 'M1同比', type: 'line', yAxisIndex: 0, data: m1, smooth: true, lineStyle: { width: 2, color: '#4751A5' }, symbol: 'circle', showSymbol: false },
        { name: 'M2同比', type: 'line', yAxisIndex: 0, data: m2, smooth: true, lineStyle: { width: 2, color: '#2aa198' }, symbol: 'circle', showSymbol: false },
        { name: 'M1-M2同比(右轴)', type: 'line', yAxisIndex: 1, data: diff, smooth: true, lineStyle: { width: 2, color: '#cb4b16' }, symbol: 'circle', showSymbol: false }
      ],
      animation: false
    };
  chart.setOption(option);
  console.log(label, { points: categories.length });
  console.timeEnd(label);
  return chart;
};
