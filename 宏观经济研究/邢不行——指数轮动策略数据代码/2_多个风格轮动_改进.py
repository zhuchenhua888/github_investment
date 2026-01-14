from function import *
import matplotlib.pyplot as plt

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 5000)  # 最多显示数据的行数
start_time = '20100601'
# 设置轮动池
name_list = ['sh000016.csv', 'sh000300.csv', 'sh000001.csv', 'sz399006.csv', 'sh000852.csv', 'sh000045.csv']

def main(name_list):
    # 设置参数
    trade_rate = 0.86 / 10000  # 场内基金万分之0.86，买卖手续费相同，无印花税
    momentum_days = 20  # 计算多少天的动量
    df = pd.read_csv('sh000300.csv', encoding='gbk', parse_dates=['candle_end_time'], usecols=['candle_end_time'])

    # 导入并计算合并数据
    for name in name_list:
        df_mini = pd.read_csv(name, encoding='gbk', parse_dates=['candle_end_time'])
        name = name.split('.')[0]
        df_mini[f'{name}_amp'] = df_mini['close'] / df_mini['close'].shift(1) - 1
        # 重命名行
        df_mini.rename(columns={'open': f'{name}_open', 'close': f'{name}_close'}, inplace=True)
        df_mini = df_mini[['candle_end_time', f'{name}_open', f'{name}_close', f'{name}_amp']]
        # 合并到一整个df中
        # df = pd.merge(df,df_mini,how='left',on=['candle_end_time'])
        df = pd.merge(df,df_mini,how='right',on=['candle_end_time'])
        df = df[df['candle_end_time'] >= pd.to_datetime(start_time)]
        # 计算N日的动量momentum
        df[f'{name}_mom'] = df[f'{name}_close'].pct_change(periods=momentum_days)
        # print(df_mini)
        # print(df.columns)
    # 生成style列
    for name in name_list:
        name = name.split('.')[0]
        df.loc[df[f'{name}_mom'] == df[[i.split('.')[0] + '_mom' for i in name_list]].max(axis=1), 'style'] = f'{name}'
    df.loc[df[[i.split('.')[0] + '_mom' for i in name_list]].max(axis=1) < 0, 'style'] = 'empty'
    # 相等时维持原来的仓位。
    df['style'].fillna(method='ffill', inplace=True)
    # 收盘才能确定风格，实际的持仓pos要晚一天。
    df['pos'] = df['style'].shift(1)
    # 删除持仓为nan的天数（创业板2010年才有）
    df.dropna(subset=['pos'], inplace=True)
    # 计算策略的整体涨跌幅strategy_amp
    for name in name_list:
        name = name.split('.')[0]
        df.loc[df['pos'] == name, 'strategy_amp'] = df[f'{name}_amp']
    df.loc[df['pos'] == 'empty', 'strategy_amp'] = 0
    # 调仓时间
    df.loc[df['pos'] != df['pos'].shift(1), 'trade_time'] = df['candle_end_time']
    # 将调仓日的涨跌幅修正为开盘价买入涨跌幅（并算上交易费用，没有取整数100手，所以略有误差）
    for name in name_list:
        name = name.split('.')[0]
        df.loc[(df['trade_time'].notnull()) & (df['pos'] == name), 'strategy_amp_adjust'] = df[f'{name}_close'] / (df[f'{name}_open'] * (1 + trade_rate)) - 1

    df.loc[df['trade_time'].isnull(), 'strategy_amp_adjust'] = df['strategy_amp']
    # 扣除卖出手续费
    df.loc[(df['trade_time'].shift(-1).notnull()) & (df['pos'] != 'empty'), 'strategy_amp_adjust'] = (1 + df[
        'strategy_amp']) * (1 - trade_rate) - 1
    del df['strategy_amp'], df['style']
    df.reset_index(drop=True, inplace=True)
    # 计算净值
    for name in name_list:
        name = name.split('.')[0]
        df[f'{name}_net'] = df[f'{name}_close'] / df[f'{name}_close'][0]
    df['strategy_net'] = (1 + df['strategy_amp_adjust']).cumprod()

    # 评估策略的好坏
    res = evaluate_investment(df, 'strategy_net', time='candle_end_time')
    print(res)

    # 绘制图形
    plt.plot(df['candle_end_time'], df['strategy_net'], label='strategy')
    for name in name_list:
        name = name.split('.')[0]
        plt.plot(df['candle_end_time'], df[f'{name}_net'], label=f'{name}_net')
    # plt.plot(df['candle_end_time'], df['small_net'], label='small_net')
    plt.show()

    # 保存文件
    # print(df.tail(10))
    df.to_csv('大小盘风格轮动_改进.csv', encoding='gbk', index=False)


if __name__ == '__main__':
    main(name_list)