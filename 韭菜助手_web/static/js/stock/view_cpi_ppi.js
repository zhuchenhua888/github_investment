window.StockViews = window.StockViews || {};
window.StockViews.renderCpiPpi = function(page) {
  if (!page || !page.data) return;
  const cpiData = page._cpiData || page.data.cpiData || [];
  const ppiData = page._ppiData || page.data.ppiData || [];
  if (!Array.isArray(cpiData) || !Array.isArray(ppiData) || cpiData.length === 0 || ppiData.length === 0) {
    console.warn('cpiData 或 ppiData 为空或未提供，跳过渲染');
    return;
  }

  const label = 'render_cpi_ppi';
  console.time(label);

  const cpiMap = new Map();
  cpiData.forEach(item => {
    const month = item.month || item.date || item.tradeDate || '';
    const yoy = parseFloat(item.national_yoy ?? item.yoy ?? item.CPIYoY ?? item.value);
    if (month && isFinite(yoy)) cpiMap.set(month, yoy);
  });
  const ppiMap = new Map();
  ppiData.forEach(item => {
    const month = item.month || item.date || item.tradeDate || '';
    const yoy = parseFloat(item.yoy ?? item.PPIYoY ?? item.value);
    if (month && isFinite(yoy)) ppiMap.set(month, yoy);
  });
  const categories = [...new Set([...cpiMap.keys(), ...ppiMap.keys()])].sort();
  const cpi = categories.map(m => (cpiMap.has(m) ? cpiMap.get(m) : null));
  const ppi = categories.map(m => (ppiMap.has(m) ? ppiMap.get(m) : null));

  // CPI-PPI 差值（右轴）
  const diff = cpi.map((cv, i) => {
    const pv = ppi[i];
    if (typeof cv === 'number' && typeof pv === 'number') return cv - pv;
    return null;
  });

  // 左右 Y 轴零点对齐（对称范围设置）
  const numsLeft = [...cpi, ...ppi].filter(v => typeof v === 'number');
  const maxAbsLeft = numsLeft.length ? Math.max(...numsLeft.map(v => Math.abs(v))) : 10;
  const numsRight = diff.filter(v => typeof v === 'number');
  const maxAbsRight = numsRight.length ? Math.max(...numsRight.map(v => Math.abs(v))) : 10;
  const pad = 1;

  const dom = document.getElementById('cpiPpiChart');
  if (!dom || !window.echarts) return;
  const chart = echarts.init(dom);
  const option = {
      //title: { text: '中国国内CPI、PPI当月同比与差值', left: 'center', top: '2%', textStyle: { fontSize: 14, color: '#686868' } },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.95)', borderColor: '#d1d9e0', borderWidth: 1, borderRadius: 8, padding: [4,4],
        textStyle: { fontSize: 13, color: '#333' },
        formatter: params => {
          const date = params[0]?.axisValue || '';
          const c = params.find(p => p.seriesName === 'CPI同比')?.data;
          const p = params.find(p => p.seriesName === 'PPI同比')?.data;
          const d = params.find(p => p.seriesName === 'CPI-PPI(右轴)')?.data;
          const fPct = v => (typeof v === 'number' ? `${v.toFixed(2)}%` : 'N/A');
          return `📅 ${date}<br/>` +
                 `CPI同比：${fPct(c)}<br/>` +
                 `PPI同比：${fPct(p)}<br/>` +
                 `CPI-PPI(右轴)：${fPct(d)}`;
        }
      },
      grid: { left: '5%', right: '5%', top: '12%', bottom: '2%', containLabel: true },
      xAxis: [{ type: 'category', data: categories, axisLine: { show: false }, axisTick: { show: false } }],
      yAxis: [
        { type: 'value', position: 'left', axisLine: { show: false }, splitLine: { show: true, lineStyle: { type: 'dashed', color: '#e0e0e0' } }, min: -(maxAbsLeft + pad), max: (maxAbsLeft + pad) },
        { type: 'value', position: 'right', axisLine: { show: false }, splitLine: { show: false }, min: -(maxAbsRight + pad), max: (maxAbsRight + pad) }
      ],
      legend: { top: '2%', left: 'center' },
      series: [
        { name: 'CPI同比', type: 'line', yAxisIndex: 0, data: cpi, smooth: true, lineStyle: { width: 2, color: '#268bd2' }, symbol: 'circle', showSymbol: false },
        { name: 'PPI同比', type: 'line', yAxisIndex: 0, data: ppi, smooth: true, lineStyle: { width: 2, color: '#2aa198' }, symbol: 'circle', showSymbol: false },
        { name: 'CPI-PPI(右轴)', type: 'line', yAxisIndex: 1, data: diff, smooth: true, lineStyle: { width: 2, color: '#b58900' }, symbol: 'circle', showSymbol: false }
      ],
      animation: false
    };
  chart.setOption(option);
  console.log(label, { points: categories.length });
  console.timeEnd(label);
  return chart;
  
}
