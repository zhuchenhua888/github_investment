def extract_convertible_bonds(text):
    # 将文本按行分割
    lines = text.split('\n')
    
    # 找到表头行，确定各列的位置
    header_line = None
    for line in lines:
        if '代码 名称 方案进展' in line:
            header_line = line
            break
    
    if header_line is None:
        return []
    
    # 分割表头，确定各列的索引（由于字段内部可能有空格，需要手动处理）
    # 这里假设表头是固定的，且字段顺序为：代码、名称、方案进展、...
    # 实际处理时，可能需要更复杂的逻辑来定位列，但这里简化处理
    
    # 初始化结果列表
    results = []
    
    # 遍历所有行，跳过表头
    current_bond = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 检查是否是新的可转债记录（以代码开头）
        if line.startswith(('60', '00', '30', '688')) and len(line.split()) >= 3:
            # 如果是新的记录，且之前有未保存的记录，先保存
            if current_bond:
                # 检查方案进展是否符合条件
                progress = current_bond.get('方案进展', '')
                if progress in ['同意注册', '上市委通过']:
                    results.append(current_bond)
            # 开始新的记录
            parts = line.split(maxsplit=2)  # 分割前3部分（代码、名称、方案进展）
            if len(parts) >= 3:
                code = parts[0]
                name = parts[1]
                progress = parts[2]
                current_bond = {
                    '代码': code,
                    '名称': name,
                    '方案进展': progress
                }
            else:
                current_bond = {}
        else:
            # 继续填充当前记录的其他字段（这里简化处理，只提取关键字段）
            # 实际可能需要更复杂的逻辑来匹配字段名和值
            pass
    
    # 处理最后一个记录
    if current_bond:
        progress = current_bond.get('方案进展', '')
        if progress in ['同意注册', '上市委通过']:
            results.append(current_bond)
    
    return results

