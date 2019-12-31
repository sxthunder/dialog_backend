import queue
import json
import os
#import logging
#logging.basicConfig(filename='info.log', level=logging.DEBUG)


def build(tuples_list, condition_children):
    condition_labels_list = []
    conditions_list = []
    condition_labels = []
    conditions = []
    statistics = ''
    cypher_list = []
    # 以or符号为界，产生两个Cypher的Union操作
    for index, condition in enumerate(condition_children):
        if condition == 'or':
            if len(condition_labels) > 0:
                condition_labels_list.append(condition_labels)
                conditions_list.append(conditions)
                condition_labels = []
                conditions = []
        elif condition == 'Statistics':
            statistics = tuples_list[index]
            tuples_list.remove(statistics)
        else:
            condition_labels.append(condition)
            conditions.append(tuples_list[index])
    condition_labels_list.append(condition_labels)
    conditions_list.append(conditions)
    statistics_type = ''
    for index, condition_labels in enumerate(condition_labels_list):
        cypher_item, statistics_type = generate(conditions_list[index], condition_labels, statistics)
        cypher_list.append(cypher_item)
    cypher = 'union\n'.join(cypher_list)
    print('########### 构建出的Cypher查询 ############')
    print(cypher)
    return cypher, statistics_type


# 生成Cypher
def generate(conditions, condition_labels, statistics):
    print('########## 开始构建Cypher ##########')
    match_ = 'match '
    where_ = 'where '
    match_list = []
    where_list = []
    condition_count = 0
    dir_name = os.path.dirname(__file__)
    concept_dict = json.load(fp=open(os.path.join(dir_name, 'dict/concept_kb.json'), encoding='utf-8'))
    variable_dict = {}.fromkeys(concept_dict.keys(), [])
    q_tuples = queue.Queue()
    q_labels = queue.Queue()
    for label in condition_labels:
        if label in ['TimeBlock', 'RelationCondition', 'PropertyCondition', 'RelationPropertyCondition']:
            condition_count += 1
        q_labels.put(label)
    for condition in conditions:
        q_tuples.put(condition)
    count = 0
    while not q_labels.empty() and not q_tuples.empty():
        label = q_labels.get()
        tuples = q_tuples.get()
        if label == 'TimeBlock':
            count += 1
            if not q_labels.empty():
                next_label = q_labels.get()
                next_tuples = q_tuples.get()
                if next_label in ['RelationCondition', 'RelationPropertyCondition']:
                    match_temp, where_temp = generate_TimeBlock(tuples, next_tuples, count, condition_count, variable_dict)
                    match_list.append(match_temp)
                    where_list.append(where_temp)
        elif label == 'RelationCondition':
            count += 1
            match_temp, where_temp = generate_RelationCondition(tuples, count, condition_count, variable_dict)
            match_list.append(match_temp)
            where_list.append(where_temp)
        elif label == 'PropertyCondition':
            count += 1
            match_temp, where_temp = generate_PropertyCondition(tuples, count, condition_count, variable_dict)
            if match_temp != '':
                match_list.append(match_temp)
            if where_temp != '':
                where_list.append(where_temp)
        elif label == 'RelationPropertyCondition':
            count += 1
            match_temp, where_temp = generate_RelationPropertyCondition(tuples, count, condition_count, variable_dict)
            match_list.append(match_temp)
            where_list.append(where_temp)
        elif label == 'concept':
            if condition_count == 0:
                count += 1
                condition_count += 1
                match_temp, where_temp = generate_concept(tuples, variable_dict)
                match_list.append(match_temp)
                if where_temp != '':
                    where_list.append(where_temp)
        elif label == 'Direction':
            pass
        print('########## 变量词典 #########')
        for item in variable_dict.items():
            print(item)
    return_, statistics_type = generate_Statistics(statistics, count)
    if len(match_list) == 0:
        match_ = ''
    if len(where_list) == 0:
        where_ = ''
    return match_ + ','.join(match_list) + '\n' + where_ + ' and '.join(where_list) + '\n' + return_ + '\n', statistics_type


# 单独概念处理
def generate_concept(tuples, variable_dict):
    concept = tuples[1]
    sub = '病人'
    where_ = ''
    if concept == sub:
        variable_dict[concept] = ['s']
        match_ = '(s:' + concept + ')'
    else:
        variable_dict[sub] = ['s']
        variable_dict[concept] = ['o']
        match_ = '(s:' + sub + ')-->(o:' + concept + ')'
    return match_, where_


# 时间块的转换
def generate_TimeBlock(timeblock_tuples, condition_tuples, count, condition_count, variable_dict):
    rc_tuples = condition_tuples
    if len(rc_tuples) > 0:
        condition_type = rc_tuples[0][3]
    word_belong_ = ''
    for item in rc_tuples:
        if item[2] == 'instance':
            word_belong_ = item[1]
            break
    property_of_concept = {
        "化验详情": "申请日期",
        "手术详情": "日期",
        "医嘱详情": "开始日期",
        "疾病详情": "日期"
    }
    word_type_list = []
    word_list = []
    match_ = ''
    for x in timeblock_tuples:
        word_type_list.append(x[2])
        word_list.append(x[0])
    if condition_type == 'RelationCondition':
        match_temp, where_temp = generate_RelationCondition(condition_tuples, count, condition_count, variable_dict)
    elif condition_type == 'RelationPropertyCondition':
        match_temp, where_temp = generate_RelationPropertyCondition(condition_tuples, count, condition_count, variable_dict)
    time_list = []
    time_direction = -1
    for x in range(len(word_type_list)):
        if word_type_list[x] == 'time':
            time_list.append(word_list[x])
        elif word_type_list[x] in ['after', 'before']:
            time_direction = word_type_list[x]
    time_start, time_end = process_time(time_list, time_direction)
    if time_direction == 'before':
        where_ = 'r' + str(count) + '.' + property_of_concept[word_belong_] + '<' + str(time_start)
    elif time_direction == 'after':
        where_ = 'r' + str(count) + '.' + property_of_concept[word_belong_] + '>' + str(time_start)
    else:
        where_temp_0 = 'r' + str(count) + '.' + property_of_concept[word_belong_] + '>' + str(time_start)
        where_temp_1 = 'r' + str(count) + '.' + property_of_concept[word_belong_] + '<' + str(time_end)
        where_ = where_temp_0 + ' and ' + where_temp_1
    if match_temp != '':
        match_ = match_temp
    return match_, where_temp + ' and ' + where_


# 关系类型条件的Cypher生成
def generate_RelationCondition(condition_tuples, count, condition_count, variable_dict):
    name_of_concept = {
        "病人": "EMPI",
        "化验详情": "名称",
        "手术详情": "名称",
        "医嘱详情": "名称",
        "疾病详情": "名称"
    }
    subject_ = ''
    object_ = ''
    instance_list = []
    not_flag = 0
    for x in condition_tuples:
        if x[2] == 'relation':
            pairs = x[1].split('.')
            subject_ = pairs[0]
            object_ = pairs[1]
        elif x[2] == 'instance':
            instance_list.append(x[0])
        elif x[2] == 'not':
            not_flag = 1
    kv_o_list = []
    for x in instance_list:
        x = "'"+x+"'"
        kv_o_list.append(x)
    if not_flag == 1:
        match_ = '(s:' + subject_ + '), (s' + str(count) + ':' + subject_ + ')-[r' + str(count) + ']->(o.indexo:object)'
        where_ = 'o.index' + '.p in ' + 'value' + ' and ' + 's.EMPI <> s' + str(count) +'.EMPI'
        match_ = match_.replace('.indexo', str(count)).replace('object', object_)
        where_ = where_.replace('.index', str(count)).replace('p', name_of_concept[object_]).replace('value', '[' + ','.join(kv_o_list) + ']')
        variable_dict[subject_] = ['s']
        temp_sub = list(variable_dict.get(subject_))
        temp_sub.append('s' + str(count))
        variable_dict[subject_] = temp_sub
        temp_obj = list(variable_dict.get(object_))
        temp_obj.append('o' + str(count))
        variable_dict[object_] = temp_obj
    else:
        match_ = '(s:' + subject_ +')-[r' + str(count) + ']->(o.indexo:object)'
        where_ = 'o.index' + '.p in ' + 'value'
        match_ = match_.replace('.indexo', str(count)).replace('object', object_)
        where_ = where_.replace('.index', str(count)).replace('p', name_of_concept[object_]).replace('value', '[' + ','.join(kv_o_list) + ']')
        variable_dict[subject_] = ['s']
        temp = list(variable_dict.get(object_))
        temp.append('o'+str(count))
        variable_dict[object_] = temp
    return match_, where_


# 属性类型条件的Cypher的生成
def generate_PropertyCondition(condition_tuples, count, condition_count, variable_dict):
    sub = '病人'
    obj = '住院信息'
    match_ = ''
    where_list = []
    word_type_list = []
    word_list = []
    word_belong_list = []
    for x in condition_tuples:
        word_type_list.append(x[2])
        word_list.append(x[0])
        word_belong_list.append(x[1])
    if len(word_type_list) > 1 and len(word_list) > 1 and len(word_belong_list) > 1:
        if word_type_list[0] == 'propertyS':
            # 处理 propertyS valueS 序列
            if word_belong_list[0] == sub:
                # 判断属性是属于病人还是住院信息
                if len(variable_dict[sub]) > 0:
                    # 该条件有前置条件，不需要增加MATCH
                    variable_s = variable_dict[sub]
                    if word_type_list[1] == 'valueS':
                        for variable in variable_s:
                            where_temp = variable + '.' + word_list[0] + '=' + "'" + word_list[1] + "'"
                            where_list.append(where_temp)
                    else:
                        pass
                else:
                    # 该条件是首个且唯一的条件，需要增加MATCH（s:病人）
                    if condition_count == 1:
                        match_ = '(s:病人)'
                    variable_dict[sub] = ['s']
                    where_temp = 's.' + word_list[0] + '=' + "'" + word_list[1] + "'"
                    where_list.append(where_temp)
            elif word_belong_list[0] == obj:
                match_ = '(s:病人)-->(o:住院信息)'
                variable_o = variable_dict[obj]
                if word_type_list[1] == 'valueS':
                    for variable in variable_o:
                        match_ = match_.replace('o', variable)
                        where_temp = variable + '.' + word_list[0] + '=' + "'" + word_list[1] + "'"
                        where_list.append(where_temp)
            else:
                # 属性在边上
                where_temp = 'r'+ str(count) + '.' + word_list[0] + '=' + "'" + word_list[1] + "'"
                where_list.append(where_temp)
        elif word_type_list[0] == 'propertyN':
            variables = ''
            if len(variable_dict[sub]) == 0 and condition_count == 1:
                match_ = '(s:病人)'
                variable_dict[sub] = ['s']
            # 处理 propertyN 序列
            if word_belong_list[0] == sub:
                # 该属性属于病人
                variables = ['s']
            elif word_belong_list[0] == obj:
                # 该属性属于住院信息
                match_ = '(s:病人)-->(o' + str(count) + ':住院信息)'
                temp = list(variable_dict.get(obj))
                temp.append('o'+str(count))
                variable_dict[obj] = temp
                variables = variable_dict[obj]
            if len(word_type_list) < 4:
                if word_type_list[1] == 'valueN':
                    for variable in variables:
                        where_temp = variable + '.' + word_list[0] + '=' + str(word_list[1])
                        where_list.append(where_temp)
                elif word_type_list[1] == 'greater' and word_type_list[2] == 'valueN':
                    for variable in variables:
                        where_temp = variable + '.' + word_list[0] + '>' + str(word_list[1])
                        where_list.append(where_temp)
                elif word_type_list[1] == 'less' and word_type_list[2] == 'valueN':
                    for variable in variables:
                        where_temp = variable + '.' + word_list[0] + '<' + str(word_list[1])
                        where_list.append(where_temp)
                elif word_type_list[1] == 'max':
                    # todo 年纪最大的患者
                    pass
                elif word_type_list[1] == 'min':
                    # todo 年纪最小的患者
                    pass
                else:
                    pass
            elif len(word_type_list) == 4:
                if word_type_list[1] == word_type_list[3] == 'valueN':
                    for variable in variables:
                        where_temp_0 = variable + '.' + word_list[0] + '>' + str(word_list[1])
                        where_temp_1 = variable + '.' + word_list[0] + '<' + str(word_list[3])
                        where_list.append(where_temp_0)
                        where_list.append(where_temp_1)
                elif word_type_list[1] == 'greater' and word_type_list[2] == 'valueN':
                    for variable in variables:
                        where_temp = variable + '.' + word_list[0] + '>' + str(word_list[2])
                        where_list.append(where_temp)
                elif word_type_list[1] == 'less' and word_type_list[2] == 'valueN':
                    for variable in variables:
                        where_temp = variable + '.' + word_list[0] + '<' + str(word_list[2])
                        where_list.append(where_temp)
                else:
                    pass
            elif len(word_type_list) == 5:
                if word_type_list[1] == word_type_list[3] == 'valueN':
                    for variable in variables:
                        where_temp_0 = variable + '.' + word_list[0] + '>' + str(word_list[1])
                        where_temp_1 = variable + '.' + word_list[0] + '<' + str(word_list[3])
                        where_list.append(where_temp_0)
                        where_list.append(where_temp_1)
                else:
                    pass
            elif len(word_type_list) > 5:
                if word_type_list[1] == word_type_list[4] == 'valueN':
                    for variable in variables:
                        where_temp_0 = variable + '.' + word_list[0] + '>' + str(word_list[1])
                        where_temp_1 = variable + '.' + word_list[0] + '<' + str(word_list[4])
                        where_list.append(where_temp_0)
                        where_list.append(where_temp_1)
                else:
                    pass
            else:
                pass
        elif word_type_list[0] == 'propertyD':
            variables = ''
            if len(variable_dict[sub]) == 0 and condition_count == 1:
                match_ = '(s:病人)'
                variable_dict[sub] = ['s']
            # 处理 propertyN 序列
            if word_belong_list[0] == sub:
                # 该属性属于病人
                variables = ['s']
            elif word_belong_list[0] == obj:
                # 该属性属于住院信息
                match_ = '(s:病人)-->(o' + str(count) + ':住院信息)'
                temp = list(variable_dict.get(obj))
                temp.append('o'+str(count))
                variable_dict[obj] = temp
                variables = variable_dict[obj]
            time_list = []
            time_direction = -1
            for x in range(len(word_type_list)):
                if word_type_list[x] == 'time':
                    time_list.append(word_list[x])
                elif word_type_list[x] in ['before', 'after']:
                    time_direction = word_type_list[x]
            time_start, time_end = process_time(time_list, time_direction)
            if time_direction == 'before':
                for variable in variables:
                    where_temp = variable + '.' + word_list[0] + '<' + str(time_start)
                    where_list.append(where_temp)
            elif time_direction == 'after':
                for variable in variables:
                    where_temp = variable + '.' + word_list[0] + '>' + str(time_start)
                    where_list.append(where_temp)
            else:
                for variable in variables:
                    where_temp_0 = variable + '.' + word_list[0] + '>' + str(time_start)
                    where_temp_1 = variable + '.' + word_list[0] + '<' + str(time_end)
                    where_list.append(where_temp_0)
                    where_list.append(where_temp_1)
        else:
            pass
    else:
        pass
    return match_, ' and '.join(where_list)


# 关系属性类型条件的Cypher生成
def generate_RelationPropertyCondition(tuples, count, condition_count, variable_dict):
    relation_tuples = []
    property_tuples = []
    for x in tuples:
        if x[2] in ['relation', 'instance']:
            relation_tuples.append(x)
        else:
            property_tuples.append(x)
    match_temp_r, where_temp_r = generate_RelationCondition(relation_tuples, count, condition_count, variable_dict)
    match_temp_p, where_temp_p = generate_PropertyCondition(property_tuples, count, condition_count, variable_dict)
    match_ = match_temp_r
    if where_temp_r == "":
        where_ = where_temp_p
    else:
        where_ = where_temp_r + ' and ' + where_temp_p
    return match_, where_


# 统计意图的Cypher生成
def generate_Statistics(statistics, count):
    name_of_concept = {
        "病人": "EMPI",
        "化验详情": "名称",
        "手术详情": "名称",
        "医嘱详情": "名称",
        "疾病详情": "名称"
    }
    sub = '病人'
    statistics_words = ['count', 'list', 'average', 'max', 'min', 'distribution', 'proportion']
    statistics_type = {}.fromkeys(statistics_words, -1)
    with_distinct = "with distinct(s) as result"
    word_list = []
    word_label_list = []
    belong_ = ''
    return_ = ''
    for x in statistics:
        word_list.append(x[0])
        if x[2] in ['concept', 'propertyN', 'propertyS', 'propertyD']:
            belong_ = x[1]
        word_label_list.append(x[2])
    if len(word_label_list) == 2:
        if belong_ == sub:
            if count == 0:
                return_ += 'match (result:' + sub + ')' + '\n'
            if word_label_list[0] == 'concept':
                if word_label_list[1] == 'count':
                    statistics_type['count'] = word_list[0]
                    return_ += 'return count(result) as final_result'
                elif word_label_list[1] == 'list':
                    statistics_type['list'] = word_list[0]
                    return_ += 'return distinct(result) as final_result'
                elif word_label_list[1] == 'distribution':
                    statistics_type['distribution'] = word_list[0]
                    return_ += 'return s.' + name_of_concept[belong_] + ' as final_result'
            elif word_label_list[0] == 'count':
                statistics_type['count'] = word_list[1]
                return_ += 'return count(result) as final_result'
            elif word_label_list[0] == 'average' and word_label_list[1] == 'propertyN':
                statistics_type['average'] = word_list[1]
                return_ += 'return avg(result.' + word_list[1] + ') as final_result'
            elif word_label_list[0] == 'max':
                statistics_type['max'] = word_list[1]
                return_ += 'return result.' + word_list[1] + ' order by result.' + word_list[
                    1] + ' desc skip 0 limit 1 as final_result'
            elif word_label_list[0] == 'min' and word_label_list[1] == 'propertyN':
                statistics_type['min'] = word_list[1]
                return_ += 'return result.' + word_list[1] + ' order by result.' + word_list[
                    1] + ' asc skip 0 limit 1 as final_result'
            elif word_label_list[0] == 'propertyN':
                if word_label_list[1] == 'distribution':
                    statistics_type['distribution'] = word_list[0]
                elif word_label_list[1] == 'proportion':
                    statistics_type['proportion'] = word_list[0]
                return_ += 'return result.' + word_list[0] + ' as final_result'
            elif word_label_list[0] == 'propertyS' and word_label_list[1] == 'distribution':
                statistics_type['distribution'] = word_list[0]
                return_ += 'return result.' + word_list[0] + ' as final_result'
            elif word_label_list[0] == 'propertyS' and word_label_list[1] == 'proportion':
                statistics_type['proportion'] = word_list[0]
                return_ += 'return result.' + word_list[0] + ' as final_result'
            else:
                pass
        else:
            match_ = 'match (s:' + sub + ')-->(o' + str(count) + ':' + belong_ + ')'
            if count > 0:
                where_ = 'where s.EMPI = result.EMPI'
                return_ = match_ + '\n' + where_ + '\n'
            else:
                return_ = match_ + '\n'
            if word_label_list[0] == 'concept':
                if word_label_list[1] == 'count':
                    statistics_type['count'] = word_list[0]
                    return_ += 'return count(o' + str(count) + ') as final_result'
                elif word_label_list[1] == 'list':
                    statistics_type['list'] = word_list[0]
                    return_ += 'return distinct(o' + str(count) + ') as final_result'
                elif word_label_list[1] == 'distribution':
                    statistics_type['distribution'] = word_list[0]
                    return_ += 'return o' + str(count) + '.' + name_of_concept[belong_] + ' as final_result'
                elif word_label_list[1] == 'proportion':
                    statistics_type['proportion'] = word_list[0]
                    return_ += 'return o' + str(count) + '.' + name_of_concept[belong_] + ' as final_result'
            elif word_label_list[0] == 'count':
                statistics_type['count'] = word_list[1]
                return_ += 'return count(o' + str(count) + ') as final_result'
            elif word_label_list[0] == 'average' and word_label_list[1] == 'propertyN':
                statistics_type['average'] = word_list[1]
                return_ += 'return avg(o' + str(count) + '.' + word_list[1] + ') as final_result'
            elif word_label_list[0] == 'max':
                statistics_type['max'] = word_list[1]
                return_ += 'return o' + str(count) + '.' + word_list[1] + ' as final_result order by result.' + word_list[
                    1] + ' desc skip 0 limit 1'
            elif word_label_list[0] == 'min' and word_label_list[1] == 'propertyN':
                statistics_type['min'] = word_list[1]
                return_ += 'return o.' + str(count)+ '.' + word_list[1] + ' order by result.' + word_list[
                    1] + ' asc skip 0 limit 1 as final_result'
            elif word_label_list[0] == 'propertyN':
                if word_label_list[1] == 'distribution':
                    statistics_type['distribution'] = word_list[0]
                elif word_label_list[1] == 'proportion':
                    statistics_type['proportion'] = word_list[0]
                return_ += 'return o' + str(count) + '.' + word_list[0] + ' as final_result'
            elif word_label_list[0] == 'propertyS':
                if word_label_list[1] == 'distribution':
                    statistics_type['distribution'] = word_list[0]
                    return_ += 'return o' + str(count) + '.' + word_list[0] + ' as final_result'
                elif word_label_list[1] == 'list':
                    statistics_type['list'] = word_list[0]
                    return_ += 'return distinct(o' + str(count) + '.' + word_list[0] + ') as final_result'
            else:
                pass
        if count > 0:
            return_ = with_distinct + '\n' + return_
    return return_, statistics_type


# 时间标准化处理
def process_time(time_list, time_direction):
    time_start = ''
    time_end = ''
    if time_direction in ['before', 'after']:
        if len(time_list) == 1:
            time_start = time_list[0]
            if time_start[6] == time_start[7] == '0':
                time_start = time_start[:7] + '1'
            if time_start[4] == time_start[5] == '0':
                time_start = time_start[:5] + '1' + time_start[6:]
    else:
        if len(time_list) == 1:
            time_start = time_list[0]
            time_end = time_list[0]
            if time_start[6] == time_start[7] == '0':
                time_start = time_start[:7] + '1'
            if time_start[4] == time_start[5] == '0':
                time_start = time_start[:5] + '1' + time_start[6:]
            if time_end[6] == time_end[7] == '0':
                time_end = time_end[:6] + '31'
            if time_end[4] == time_end[5] == '0':
                time_end = time_end[:5] + '12' + time_end[6:]
        elif len(time_list) == 2:
            time_start = time_list[0]
            time_end = time_list[1]
            if len(time_start) == len(time_end) == 8:
                if time_start[6] == time_start[7] == '0':
                    time_start = time_start[:7] + '1'
                if time_start[4] == time_start[5] == '0':
                    time_start = time_start[:5] + '1' + time_start[6:]
                if time_end[6] == time_end[7] == '0':
                    time_end = time_end[:6] + '31'
                if time_end[4] == time_end[5] == '0':
                    time_end = time_end[:4] + '12' + time_end[6:]
        else:
            pass
    return time_start, time_end
