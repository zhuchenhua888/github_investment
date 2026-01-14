window.PageAdapter = {
  create(currentData) {
    const data = {
      hushen300Data: currentData.hushen300Data || [],
      bondYieldData: currentData.bondYieldData || [],
      gdpData: currentData.gdpData || [],
      stockMarketData: currentData.stockMarketData || [],
      buffetData: currentData.buffetData || [],
      fedPremiumData: currentData.fedPremiumData || null,
      riskPremiumData: currentData.riskPremiumData || null,
      moneySupplyData: currentData.moneySupplyData || [],
      cpiData: currentData.cpiData || [],
      ppiData: currentData.ppiData || [],
      marginAccountInfoData: currentData.marginData || []
    };
    return {
      data,
      _hushen300Data: data.hushen300Data,
      _bondYieldData: data.bondYieldData,
      _chinaGDPData: data.gdpData,
      _chinaStockMarketData: data.stockMarketData,
      _buffetData: data.buffetData,
      _fedPremiumData: data.fedPremiumData,
      _riskPremiumData: data.riskPremiumData,
      _moneySupplyData: data.moneySupplyData,
      _cpiData: data.cpiData,
      _ppiData: data.ppiData,
      _marginAccountInfoData: data.marginAccountInfoData
    };
  }
};
