// 适配Web系统的帮助信息管理
window.StockHelp = {
    getHelpData: function(type) {
        let title = '';
        let content = '';

        switch (type) {
            case 'moneySupply':
                title = '货币供应说明';
                content = this.getMoneySupplyHelpHtml();
                break;
            case 'riskPremium':
                title = '风险溢价说明';
                content = this.getRiskBondHelpHtml();
                break;
            case 'stockBond':
                title = '股债比说明';
                content = this.getRiskBondHelpHtml();
                break;
            case 'buffet':
                title = '巴菲特指标说明';
                content = this.getBuffetHelpHtml();
                break;
            case 'margin':
                title = '两融账户信息说明';
                content = this.getMarginHelpHtml();
                break;
            case 'inflation':
                title = '通货膨胀说明';
                content = this.getInflationHelpHtml();
                break;
            default:
                title = '帮助信息';
                content = '<p>暂无详细说明。</p>';
        }

        return { title, content };
    },

    getMoneySupplyHelpHtml: function() {
        return (
            `<div style="font-size:14px;line-height:1.6;">
        <h3 style="font-size:15px;margin:12px 0;"><b>一、M1 vs M2：</b></h3>
        <ul style="padding-left:20px;">
          <li><b>M1</b>：现金 + 活期存款（<b>现在能花的钱</b>）</li>
          <li><b>M2</b>：M1 + 定期存款等（<b>现在+未来能花的钱</b>）</li>
          <li><b>核心区别</b>：M1是“即时购买力”，M2是“总货币量”。</li>
        </ul>

        <h3 style="font-size:15px;margin:12px 0;"><b>二、M2增长与股市的关系</b></h3>
        <h4 style="font-size:14px;margin:8px 0;"><b>1. 钱怎么进股市？</b></h4>
        <ul style="padding-left:20px;">
          <li><b>直接</b>：M2↑ → 社会钱变多 → 多余钱可能买股票。</li>
          <li><b>间接</b>：
            <ul style="padding-left:20px;">
              <li>利率↓（存款收益低）→ 钱转投股市。</li>
              <li>通胀预期↑ → 股票抗通胀 → 资金涌入。</li>
              <li>企业融资成本↓ → 盈利预期↑ → 股价涨。</li>
            </ul>
          </li>
        </ul>
        <h4 style="font-size:14px;margin:8px 0;"><b>2. 比值（M2/股市市值）看风险</b></h4>
        <ul style="padding-left:20px;">
          <li><b>比值低</b>：钱多但没进股市（可能去买房/实体）→ 股市低估或资金分流。</li>
          <li><b>比值高</b>：钱过度进股市 → 警惕泡沫（如2015年股灾前）。</li>
        </ul>

        <h3 style="font-size:15px;margin:12px 0;"><b>三、M1-M2增速差：经济温度计</b></h3>
        <h4 style="font-size:14px;margin:8px 0;"><b>1. 增速差收窄（M1↑快于M2↑）</b></h4>
        <ul style="padding-left:20px;">
          <li><b>信号</b>：企业敢投资、居民敢消费 → 流动性提升。</li>
          <li><b>对股市</b>：利好（企业盈利改善，资金入市）。</li>
          <li><b>案例</b>：2016-2017年中国M1-M2差扩大 → 股市涨（周期股领涨）。</li>
        </ul>
        <h4 style="font-size:14px;margin:8px 0;"><b>2. 增速差扩大（M1↓慢于M2↑）</b></h4>
        <ul style="padding-left:20px;">
          <li><b>信号</b>：企业存定期、居民多储蓄 → 投资消费意愿低。</li>
          <li><b>对股市</b>：利空（资金撤离，盈利下滑）。</li>
          <li><b>案例</b>：2018年中国M1增速跌至低位 → 股市全年下跌。</li>
        </ul>

        <h3 style="font-size:15px;margin:12px 0;"><b>四、关键提醒：别只看数字！</b></h3>
        <ul style="padding-left:20px;">
          <li><b>要结合看</b>：GDP、CPI、信贷数据（避免误判）。</li>
          <li><b>警惕短期波动</b>：春节前现金需求可能扭曲M1数据（看3-6个月趋势）。</li>
          <li><b>政策影响大</b>：央行降准/加息会直接改变M1-M2结构。</li>
        </ul>

        <h3 style="font-size:15px;margin:12px 0;"><b>五、一句话总结</b></h3>
        <ul style="padding-left:20px;">
          <li><b>M1-M2收窄</b>：经济热、股市可能涨（但需确认钱是否真进股市）。</li>
          <li><b>M1-M2扩大</b>：经济冷、股市可能跌（需防衰退风险）。</li>
          <li><b>比值极端高低</b>：低=机会？高=泡沫？需结合估值和政策。</li>
        </ul>
      </div>`
        );
    },

    getRiskBondHelpHtml: function() {
        return (
            `<div style="font-size:14px;line-height:1.6;">
      <h3 style="font-size:15px;margin:12px 0;"><b>一、核心模型：股票 vs 债券的性价比</b></h3>
      <h4 style="font-size:14px;margin:8px 0;"><b>1. 风险溢价模型</b></h4>
      <ul style="padding-left:20px;">
        <li><b>公式</b>：风险溢价 = 1/沪深300市盈率 - 10年期国债收益率（即：股票盈利收益率 - 无风险收益率）</li>
        <li><b>逻辑</b>：
          <ul style="padding-left:20px;">
            <li>股票盈利收益率（市盈率倒数）代表投资股票的预期回报率。</li>
            <li>国债收益率代表无风险收益基准。</li>
            <li><b>差值越大</b>：股票相对债券越有吸引力（如风险溢价=3%时，股票比债券多赚3%）。</li>
            <li><b>差值越小</b>：债券性价比更高（如风险溢价=0%时，两者收益相当）。</li>
          </ul>
        </li>
        <li><b>实战参考</b>：历史经验：当风险溢价>1%时，股市长期回报可能优于债券；极端情况：2014年风险溢价达6%（股市低估），2018年接近0%（股市高估）。</li>
      </ul>
      <h4 style="font-size:14px;margin:8px 0;"><b>2. 股债比模型</b></h4>
      <ul style="padding-left:20px;">
        <li><b>公式</b>：股债比 = (1/沪深300市盈率) / 10年期国债收益率（即：股票盈利收益率 ÷ 无风险收益率）</li>
        <li><b>逻辑</b>：
          <ul style="padding-left:20px;">
            <li>比值>1：股票预期回报高于债券，投资股票性价比更高。</li>
            <li>比值<1：债券更安全且收益不输股票。</li>
            <li><b>比值越大</b>：股票吸引力越强（如比值=1.5时，股票收益比债券高50%）。</li>
          </ul>
        </li>
        <li><b>案例</b>：2020年3月股债比升至1.3（疫情后利率暴跌，股票估值低位），随后股市反弹；2021年股债比跌至0.8（核心资产泡沫），股市随后调整。</li>
      </ul>
      <h3 style="font-size:15px;margin:12px 0;"><b>二、利率与股市的跷跷板</b></h3>
      <h4 style="font-size:14px;margin:8px 0;"><b>1. 利率下调的影响</b></h4>
      <ul style="padding-left:20px;">
        <li><b>资金流向</b>：利率↓ → 债券收益↓ → 资金从债市流向股市；利率↓ → 企业融资成本↓ → 盈利改善 → 股价上涨。</li>
        <li><b>历史规律</b>：2015年央行5次降息 → 沪深300全年涨15%；2020年LPR下调 → 股市快速修复。</li>
      </ul>
      <h4 style="font-size:14px;margin:8px 0;"><b>2. 关键阈值：比值=1的临界点</b></h4>
      <ul style="padding-left:20px;">
        <li><b>当股债比=1（或风险溢价=0%）时</b>：理论上股票与债券收益相同，但股票承担更高风险，理性投资者应选择债券；现实中市场可能因情绪或政策继续上涨，但长期回报率趋近零。</li>
        <li><b>策略建议</b>：比值<1时，降低股票仓位，增配债券或现金；比值>1.2时，可逐步加仓股票（尤其高股息品种）。</li>
      </ul>
      <h3 style="font-size:15px;margin:12px 0;"><b>三、模型应用中的注意事项</b></h3>
      <ol style="padding-left:20px;">
        <li><b>动态调整</b>：比值/差值需结合市场阶段与政策变化；例如牛市后期股债比可能长期<1，但情绪推动股价继续上涨。</li>
        <li><b>风险补偿</b>：比值模型隐含“风险溢价”，实际需考虑波动率（熊市中投资者可能要求更高比值才入场）。</li>
        <li><b>国际对比</b>：发达国家股债比均值可能低于中国（因利率长期低位），需参考历史区间。</li>
      </ol>
      <h3 style="font-size:15px;margin:12px 0;"><b>四、总结</b></h3>
      <ul style="padding-left:20px;">
        <li><b>比值模型</b>（股债比>1）：股票性价比高，可加仓。</li>
        <li><b>差值模型</b>（风险溢价>1%）：股票相对债券有超额收益。</li>
        <li><b>临界点</b>（比值=1或风险溢价=0%）：警惕股市高估，转向防御。</li>
        <li><b>核心逻辑</b>：利率决定资金成本，比值/差值反映资金选择，最终回归“风险与收益的平衡”。</li>
      </ul>
    </div>`
        );
    },

    getBuffetHelpHtml: function() {
        return (
            `<div style="font-size:14px;line-height:1.6;">
      <h3 style="font-size:15px;margin:12px 0;"><b>一、巴菲特指数：是什么？</b></h3>
      <p><b>定义</b>：巴菲特指数 = <b>A股总市值 ÷ GDP</b>（反映股市与经济总量的关系，衡量整体估值水平）</p>
      <p><b>核心逻辑</b>：</p>
      <ul style="padding-left:20px;">
        <li>股市总市值↑ → 指数↑ → 市场可能高估</li>
        <li>GDP↑（经济扩张）→ 指数↓ → 市场可能低估</li>
      </ul>
      <p><b>📌关键结论</b>：指数越高，股市越“贵”；越低，越“便宜”。</p>
      <hr/>
      <h3 style="font-size:15px;margin:12px 0;"><b>二、估值区间：多少算合理？</b></h3>
      <p><b>🔹 低估区（<70%）</b>：市场被严重低估，机会大；<b>案例</b>：2018年底部时，指数≈50%，随后开启牛市</p>
      <p><b>🔹 合理区（70%~90%）</b>：估值正常，可保持仓位；<b>当前状态（2025年9月）</b>：A股总市值104万亿 ÷ GDP 138万亿 ≈ <b>75%</b>（合理区间）</p>
      <p><b>🔹 高估区（>90%）</b>：警惕泡沫，需减仓；<b>极端案例</b>：2007年上证6124点时，指数达<b>162%</b>；2015年5178点时，指数约<b>103%</b></p>
      <p><b>📌关键结论</b>：<70%：抄底信号；70%~90%：持有观望；>90%：撤退预警</p>
      <hr/>
      <h3 style="font-size:15px;margin:12px 0;"><b>三、A股适用性：现在能用吗？</b></h3>
      <p><b>早期局限（2000-2010年）</b>：大量公司未上市 → 分子（市值）小，分母（GDP）大 → 指数天然偏低，参考价值低</p>
      <p><b>当前适用（2020年后）</b>：规模企业基本上市（仅华为等极少数例外）；<b>结论</b>：指数参考价值显著提升</p>
      <p><b>📌关键结论</b>：早期慎用，现在可用，但需结合其他指标（如市盈率、股债利差）。</p>
      <hr/>
      <h3 style="font-size:15px;margin:12px 0;"><b>四、实战建议：怎么用？</b></h3>
      <p><b>1. 长期趋势判断</b>：看3~5年大方向，别盯短期波动；<b>案例</b>：2018年指数50% → 2021年涨至90%+（长期机会）</p>
      <p><b>2. 搭配其他指标</b>：单看巴菲特指数易误判，需结合估值分位点（如沪深300历史PE）、股债利差（股票收益-国债收益）</p>
      <p><b>3. 避免个股误用</b>：指数衡量“全国大盘”，非单只股票；<b>错误用法</b>：用指数判断某股是否该买</p>
      <p><b>📌关键结论</b>：长期+综合指标=更稳决策；指数是“温度计”，不是“精确尺”。</p>
      <hr/>
      <h3 style="font-size:15px;margin:12px 0;"><b>五、总结</b></h3>
      <p><b>🔥 巴菲特指数核心口诀</b>：<b>“<70%敢买，70%~90%持有，>90%快跑”</b>（但别单押它，结合市盈率、股债利差更靠谱！）</p>
    </div>`
        );
    },

    getMarginHelpHtml: function() {
        return (
            `<div style="font-size:14px;line-height:1.6;">
      <h3 style="font-size:15px;margin:12px 0;"><b>一、融资融券余额：是什么？</b></h3>
      <p><b>定义</b>：投资者向券商借资金（融资）或借证券（融券）交易后，未还的金额。</p>
      <p><b>分两部分</b>：</p>
      <ul style="padding-left:20px;">
        <li><b>融资余额</b>：借钱买股未还的钱</li>
        <li><b>融券余额</b>：借股卖出未还的股</li>
      </ul>
      <p><b>📌 关键结论</b>：余额↑=市场杠杆↑=波动可能↑</p>
      <hr/>

      <h3 style="font-size:15px;margin:12px 0;"><b>二、融资余额：反映啥？</b></h3>
      <p><b>逻辑链</b>：融资余额↑ → 投资者借钱买股多 → 预期股价涨 → 市场乐观</p>
      <p><b>数据信号</b>：</p>
      <ul style="padding-left:20px;">
        <li>融资余额↑ → 买方强 → 市场可能涨</li>
        <li>融资余额↓ → 买方弱 → 市场可能跌</li>
      </ul>
      <p><b>📊 案例</b>：</p>
      <ul style="padding-left:20px;">
        <li>2025年11月10日：A股融资余额24831.56亿，环比↑0.31% → 市场偏乐观</li>
        <li>2020年牛市：融资余额连续3月↑ → 指数涨超30%</li>
      </ul>
      <p><b>📌 关键结论</b>：融资↑=买方强=看涨信号</p>
      <hr/>

      <h3 style="font-size:15px;margin:12px 0;"><b>三、融券余额：反映啥？</b></h3>
      <p><b>逻辑链</b>：融券余额↑ → 投资者借股卖出多 → 预期股价跌 → 市场悲观</p>
      <p><b>数据信号</b>：</p>
      <ul style="padding-left:20px;">
        <li>融券余额↑ → 卖方强 → 市场可能跌</li>
        <li>融券余额↓ → 卖方弱 → 市场可能涨</li>
      </ul>
      <p><b>📊 案例</b>：</p>
      <ul style="padding-left:20px;">
        <li>2025年11月10日：A股融券余额182.61亿，环比↑0.52% → 卖方力量小增</li>
        <li>2015年股灾前：融券余额1周↑50% → 指数1月跌45%</li>
      </ul>
      <p><b>📌 关键结论</b>：融券↑=卖方强=看跌信号</p>
      <hr/>

      <h3 style="font-size:15px;margin:12px 0;"><b>四、余额差值：市场风向标</b></h3>
      <p><b>定义</b>：融资余额 - 融券余额 = 净买入力量</p>
      <p><b>逻辑链</b>：</p>
      <ul style="padding-left:20px;">
        <li>差值↑ → 买方远强于卖方 → 市场上涨概率高</li>
        <li>差值↓ → 卖方接近或强于买方 → 市场下跌风险大</li>
      </ul>
      <p><b>📊 案例</b>：</p>
      <ul style="padding-left:20px;">
        <li>2025年11月6日：科创板融资余额2598.53亿↑37.87亿，融券9.55亿↑0.2亿 → 差值扩大 → 科创板涨</li>
        <li>2018年熊市：融资余额连降6月，融券余额稳 → 差值缩至负 → 指数跌25%</li>
      </ul>
      <p><b>📌 关键结论</b>：差值↑=买方碾压=做多机会</p>
      <hr/>

      <h3 style="font-size:15px;margin:12px 0;"><b>五、实战建议：怎么用？</b></h3>
      <p><b>1. 看趋势</b>：</p>
      <ul style="padding-left:20px;">
        <li>融资余额连涨3天 → 短期可能涨</li>
        <li>融券余额单日暴增20% → 警惕回调</li>
      </ul>
      <p><b>2. 盯行业</b>：</p>
      <ul style="padding-left:20px;">
        <li>科创板融资余额↑快 → 科技股机会</li>
        <li>消费板块融券余额↑ → 暂时回避</li>
      </ul>
      <p><b>3. 避风险</b>：</p>
      <ul style="padding-left:20px;">
        <li>融资余额/总市值>5% → 杠杆过高，慎入</li>
        <li>融券余额/流通股本>1% → 抛压重，小心</li>
      </ul>
      <p><b>📌 关键结论</b>：融资看多，融券看空，差值定方向</p>
      <hr/>

      <h3 style="font-size:15px;margin:12px 0;"><b>六、总结</b></h3>
      <p><b>🔥 融资融券核心口诀</b>：<b>“融资涨=买方强=可做多；融券升=卖方狠=要小心；差值大=方向明！”</b></p>
    </div>`
        );
    },

    getInflationHelpHtml: function() {
        return (
            `<div style="font-size:14px;line-height:1.6;">
      <h3 style="font-size:15px;margin:12px 0;"><b>一、通货膨胀指标：CPI 与 PPI</b></h3>
      <ul style="padding-left:20px;">
        <li><b>CPI</b>：居民消费价格指数，反映居民购买的商品与服务价格变动。</li>
        <li><b>PPI</b>：工业生产者出厂价格指数，反映上游出厂价格变化。</li>
        <li><b>关系</b>：PPI常领先CPI（上游成本 → 传导到消费端）。</li>
      </ul>

      <h3 style="font-size:15px;margin:12px 0;"><b>二、CPI-PPI差值：通胀结构的温度计</b></h3>
      <ul style="padding-left:20px;">
        <li><b>差值>0</b>：消费端涨幅高于上游，需求较强或服务通胀偏高。</li>
        <li><b>差值<0</b>：上游涨幅高于消费端，成本压力向下游传导。</li>
        <li><b>应用</b>：观察差值与其趋势，判断通胀结构与经济阶段。</li>
      </ul>

      <h3 style="font-size:15px;margin:12px 0;"><b>三、利率与资产：通胀周期下的配置思路</b></h3>
      <ul style="padding-left:20px;">
        <li><b>通胀上行</b>：利率上行概率↑，成长股估值受压，高股息/资源品受益。</li>
        <li><b>通胀下行</b>：利率下行概率↑，成长/科技估值修复，债券性价比提升。</li>
        <li><b>核心</b>：结合利率、经济增速与企业盈利同步判断。</li>
      </ul>

      <h3 style="font-size:15px;margin:12px 0;"><b>四、观察建议</b></h3>
      <ul style="padding-left:20px;">
        <li>关注3-6个月趋势，不以单月数据结论。</li>
        <li>结合就业、零售、房地产等数据交叉验证。</li>
        <li>关注政策与国际大宗价格的链式影响。</li>
      </ul>

      <h3 style="font-size:15px;margin:12px 0;"><b>五、总结</b></h3>
      <ul style="padding-left:20px;">
        <li>CPI与PPI组合可刻画通胀结构与阶段。</li>
        <li>差值与趋势比绝对数值更重要。</li>
        <li>资产配置需与利率周期和盈利周期匹配。</li>
      </ul>
    </div>`
        );
    }
};
