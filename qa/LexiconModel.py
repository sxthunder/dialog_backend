"""
实体链接层-单词词义化
文法构造预处理，以产生式为基准补充词项

词义定义
name    单词原值
std_name标准名称
type    单词类型: concept instance attribute relation value[number-value datetime-value string-value atom(and/or/before/after/separator)]
belong  所属: InstanceBlgConcept AttributeBlgConcept ConceptRelationConcept ValueBlgAttribute
index   序列下标
"""
# todo 未登录词待解决
import json
import re
import os
#import logging
#logging.basicConfig(filename='info.log', level=logging.DEBUG)


class LexiconEntry:
    name = ''
    std_name = ''
    type = ''
    belong = 'null'
    index = -1

    def __init__(self, name, std_name, type, belong, index):
        self.name = name
        self.std_name = std_name
        self.type = type
        self.belong = belong
        self.index = index
dir_name = os.path.dirname(__file__)
concept_dict = json.load(fp=open(os.path.join(dir_name, 'dict/concept_kb.json'), encoding='utf-8'))
attribute_dict = json.load(fp=open(os.path.join(dir_name, 'dict/property_kb.json'), encoding='utf-8'))
instance_dict = json.load(fp=open(os.path.join(dir_name, 'dict/instance_kb.json'), encoding='utf-8'))
relation_dict = json.load(fp=open(os.path.join(dir_name, 'dict/relation_kb.json'), encoding='utf-8'))
atom_dict = json.load(fp=open(os.path.join(dir_name, 'dict/atom_kb.json'), encoding='utf-8'))
string_value_dict = json.load(fp=open(os.path.join(dir_name, 'dict/value_string_kb.json'), encoding='utf-8'))
statistics_dict = json.load(fp=open(os.path.join(dir_name, 'dict/statistics_kb.json'), encoding='utf-8'))


# 识别概念
def identify_concept(index, word):
    lexical = -1
    for key, concepts in concept_dict.items():
        if word in concepts:
            lexical = LexiconEntry(name=word, std_name=key, type='concept', belong=key, index=index)
            print_lexical(lexical)
            break
    return lexical


# 识别属性
def identify_property(index, word):
    lexical = -1
    for key, attributes in attribute_dict.items():
        flag = 0
        for std_name, synonym_name in attributes.items():
            if word == std_name or word in synonym_name:
                key_set = key.split(".")
                lexical = LexiconEntry(name=word, std_name=std_name, type=key_set[0], belong=key_set[1],
                                       index=index)
                print_lexical(lexical)
                flag = 1
                break
        if flag == 1:
            break
    return lexical


# 识别关系
def identify_relation(index, word):
    lexical = -1
    for key, relations in relation_dict.items():
        flag = 0
        for std_name, synonym_names in relations.items():
            if word == std_name or word in synonym_names:
                lexical = LexiconEntry(name=word, std_name=std_name, type='relation', belong=key, index=index)
                print_lexical(lexical)
                flag = 1
                break
        if flag == 1:
            break
    return lexical


# 识别实例
def identify_instance(index, word, lexical_array, seq_que):
    lexical = -1
    lexical_length = len(lexical_array)
    for key, instances in instance_dict.items():
        flag = 0
        for std_name, synonym_name in instances.items():
            if word == std_name or word in synonym_name:
                key_set = key.split(".")
                if lexical_length > 0:
                    last_word = lexical_array[-1]  # 取得上一个词的类型
                    is_words = ['relation', 'and', 'or']
                    if last_word.type in is_words:
                        lexical = LexiconEntry(name=word, std_name=word, type='instance', belong=key_set[1],
                                               index=index)
                        print_lexical(lexical)
                    else:  # 若上一个词类型不是‘relation’‘and’‘or’或 'unknown'，上位补充一个关系类型的词项
                        lexical_add = identify_relation(index=-1, word=key_set[0])
                        if lexical_add != -1:
                            lexical_array.append(lexical_add)
                        else:
                            print("add default relation error!")
                        lexical = LexiconEntry(name=word, std_name=word, type='instance', belong=key_set[1],
                                               index=index)
                        print_lexical(lexical)
                    lexical_array = merge_or_split_and(index, lexical, lexical_array, seq_que)

                # 若没有上一个词
                else:
                    lexical_add = identify_relation(index=-1, word=key_set[0])
                    if lexical_add != -1:
                        lexical_array.append(lexical_add)
                    else:
                        print("add default relation error!")
                    lexical = LexiconEntry(name=word, std_name=word, type='instance', belong=key_set[1],
                                           index=index + 1)
                    print_lexical(lexical)
                flag = 1
                break
        if flag == 1:
            break
    return lexical


# 识别原子词
def identify_atom(index, word, lexical_array):
    lexical = -1
    for key, atoms in atom_dict.items():
        if word in atoms:
            lexical = LexiconEntry(name=word, std_name=word, type=key, belong='atom', index=index)
            print_lexical(lexical)
            supplement_property_for_propvalue(lexical=lexical, lexical_array=lexical_array)
            break
    return lexical


# 识别数值
def identify_number_value(index, word):
    lexical = -1
    number_value = re.compile(r'\d+|\d+\.\d+')
    if number_value.match(word) and len(word) != 8:
        lexical = LexiconEntry(name=word, std_name=word, type='valueN', belong='atom', index=index)
        print_lexical(lexical)
    return lexical


# 识别时间
def identify_datetime_value(index, word):
    lexical = -1
    datetime_value = re.compile(r'\d{8}')
    if datetime_value.match(word):
        lexical = LexiconEntry(name=word, std_name=word, type='time', belong='atom', index=index)
        print_lexical(lexical)
    return lexical


# 识别特定字符串
def identify_string_value(index, word, lexical_array):
    lexical = -1
    for key, values in string_value_dict.items():
        for std_name, synonym_name in values.items():
            if word == std_name or word in synonym_name:
                if len(lexical_array) > 0:
                    last_lexical = lexical_array[-1]  # 取得上一个词的类型
                    if last_lexical.type == 'propertyS':
                        lexical = LexiconEntry(name=word, std_name=std_name, type='valueS', belong='atom',
                                               index=index)
                        print_lexical(lexical)
                    else:  # 如果上个单词类型不是‘propertyS’,补全属性
                        lexical_default = identify_property(index=-1, word=key)
                        if lexical_default != -1:
                            lexical_array.append(lexical_default)
                        else:
                            print('add default property error')
                        lexical = LexiconEntry(name=word, std_name=std_name, type='valueS', belong='atom',
                                               index=index)
                        print_lexical(lexical)
                    break
                else:
                    lexical_default = identify_property(index=-1, word=key)
                    if lexical_default != -1:
                        lexical_array.append(lexical_default)
                    else:
                        print('add default property error')
                    lexical = LexiconEntry(name=word, std_name=std_name, type='valueS', belong='atom',
                                           index=index)
                    print_lexical(lexical)
                    break
    return lexical


# 识别统计词
def identify_statistics(index, word, lexical_array):
    lexical = -1
    for key, statistics in statistics_dict.items():
        if word in statistics:
            if len(lexical_array) > 0:
                last_word_type = lexical_array[-1].type  # 取得上一个词的类型
                last_word_stdname = lexical_array[-1].std_name  # 取得上一个词的标准名称
                if last_word_type == 'concept' or last_word_type.find('property') != -1:
                    lexical = LexiconEntry(name=word, std_name=statistics[0], type=key, belong='statistics',
                                           index=index)
                    print_lexical(lexical)
                else:
                    lexical = LexiconEntry(name=word, std_name=statistics[0], type=key, belong='statistics',
                                           index=index)
                    print_lexical(lexical)
                break
            else:
                lexical = LexiconEntry(name=word, std_name=statistics[0], type=key, belong='unknown',
                                       index=index)
                print_lexical(lexical)
                break
    return lexical


# 为属性值补充属性
def supplement_property_for_propvalue(lexical, lexical_array):
    if lexical.type == 'unit':
        if lexical.std_name == '岁':
            lens = len(lexical_array)
            type_list = []
            for item in lexical_array:
                type_list.append(item.type)
            type_lens = len(type_list)
            if type_lens == 1:
                if type_list[0] == 'valueN':
                    # ['valueN'] ==> ['propertyN','valueN']
                    lexical_add = identify_property(index=-1, word='年龄')
                    if lexical_add != -1:
                        lexical_array.insert(lens - 1, lexical_add)
                    else:
                        print('add default property error')
            elif type_lens == 2:
                if type_list[1] == 'valueN' and type_list[0] in ['greater', 'less']:
                    # ['greater/less','valueN'] ==> ['propertyN','greater/less','valueN']
                    lexical_add = identify_property(index=-1, word='年龄')
                    if lexical_add != -1:
                        lexical_array.insert(lens - 2, lexical_add)
                    else:
                        print('add default property error')
            elif type_lens == 3:
                if type_list[2] == 'valueN':
                    if type_list[1] == 'separator' and type_list[0] == 'valueN':
                        # ['valueN','separator','valueN'] ==> ['propertyN','valueN','separator','valueN']
                        lexical_add = identify_property(index=-1, word='年龄')
                        if lexical_add != -1:
                            lexical_array.insert(lens - 3, lexical_add)
                        else:
                            print('add default property error')
                    elif type_list[1] in ['greater', 'less'] and type_list[0] != 'propertyN':
                        # ['other', 'greater/less', 'valueN']
                        lexical_add = identify_property(index=-1, word='年龄')
                        if lexical_add != -1:
                            lexical_array.insert(lens - 3, lexical_add)
                        else:
                            print('add default property error')
            elif type_lens >= 4:
                if type_list[type_lens-1] == 'valueN':
                    if type_list[type_lens-2] in ['greater', 'less'] and type_list[type_lens-3] != 'propertyN':
                        lexical_add = identify_property(index=-1, word='年龄')
                        if lexical_add != -1:
                            lexical_array.insert(lens - 2, lexical_add)
                        else:
                            print('add default property error')
                elif type_list[type_lens-2] == 'separator' and type_list[type_lens-3] == 'valueN' and type_list[type_lens-4] != 'propertyN':
                    # ['other','valueN','separator','valueN'] ==> ['other','propertyN','valueN','separator','valueN']
                    lexical_add = identify_property(index=-1, word='年龄')
                    if lexical_add != -1:
                        lexical_array.insert(lens - 4, lexical_add)
                    else:
                        print('add default property error')
        elif lexical.std_name == '年':
            pass
        else:
            pass


# 为关系补充实例
def supplement_instance_for_relation(index, lexical, seq_que, lexical_array):
    lexical_next_ins = identify_instance(index=index+1, word=seq_que[index+1], lexical_array=lexical_array, seq_que=seq_que)
    lexical_next_con = identify_concept(index=index+1, word=seq_que[index+1])
    concept_words = lexical.belong
    concepts = concept_words.split(".")
    if lexical_next_ins != -1:
        pass
    elif lexical_next_con != -1:
        if len(concepts) == 2:
            if concepts[1] == lexical_next_con.std_name:
                pass
            else:
                lexical_concept = identify_concept(index=-1, word=concepts[1])
                lexical_array.append(lexical_concept)
    else:
        if len(concepts) == 2:
            lexical_concept = identify_concept(index=-1, word=concepts[1])
            lexical_array.append(lexical_concept)


# 为实例补充关系
def supplement_relation_for_instance(instance_std_name, lexical_array):
    for key, instances in instance_dict.items():
        flag = 0
        for std_name, synonym_name in instances.items():
            if instance_std_name == std_name or std_name in synonym_name:
                key_set = key.split(".")
                if len(key_set) == 2:
                    relation = key_set[0]
                    lexical_relation = identify_relation(-1, relation)
                    lexical_array.append(lexical_relation)
                    flag = 1
        if flag == 1:
            break
    return lexical_array


# 合并同类型的or关系，拆分同类型的and关系
def merge_or_split_and(index, lexical, lexical_array, seq_que):
    lexical_belong = lexical.belong
    lexical_length = len(lexical_array)
    if lexical_length > 2:
        # todo merge or, split and
        last_word = lexical_array[lexical_length-1]
        second_last_word = lexical_array[lexical_length - 2]
        if last_word.type == 'relation':
                if second_last_word.type == 'instance':
                    # add 'and'
                    lexical_array.insert(lexical_length-1, LexiconEntry(name='and', std_name='and',
                                                                             type='and', belong='atom', index=-1))
                    return lexical_array
                elif lexical_length > 3 and second_last_word.type == 'not':
                    third_last_word = lexical_array[lexical_length - 3]
                    if third_last_word.type == 'instance' and third_last_word.belong == lexical.belong:
                        lexical_array.insert(lexical_length - 2, LexiconEntry(name='and', std_name='and',
                                                                              type='and', belong='atom', index=-1))
                        return lexical_array
                    elif third_last_word.type == 'or' and lexical_length > 5:
                        if lexical_array[lexical_length-6].type == 'not' and lexical_array[lexical_length-4].belong == \
                                lexical.belong:
                            lexical_array.remove(lexical_array[-1])  # remove R
                            lexical_array.remove(lexical_array[-1])  # remove N
                            return lexical_array
                        else:
                            return lexical_array
                    else:
                        return lexical_array
                elif lexical_length > 3 and second_last_word.type == 'or':
                    if index+1 < len(seq_que):
                        if lexical_length > 4 and lexical_array[lexical_length - 5].type == 'and':
                            return lexical_array
                        else:
                            next_lexical = identify_atom(-1, seq_que[index + 1], lexical_array)
                            if next_lexical != -1 and next_lexical.type == 'and':
                                return lexical_array
                            else:
                                third_last_word = lexical_array[lexical_length - 3]
                                # remove R
                                if third_last_word.belong == lexical.belong:
                                    lexical_array.remove(lexical_array[-1])
                                return lexical_array
                    else:
                        third_last_word = lexical_array[lexical_length - 3]
                        # remove R
                        if third_last_word.belong == lexical.belong:
                            lexical_array.remove(lexical_array[-1])
                        return lexical_array
                else:
                    return lexical_array
        elif last_word.type == 'and':
            # add R
            if second_last_word.type == 'instance' and second_last_word.belong == lexical.belong:
                lexical_array = supplement_relation_for_instance(lexical.std_name, lexical_array)
                return lexical_array
            else:
                return lexical_array
        elif last_word.type == 'or':
            if lexical_length > 3 and lexical_array[lexical_length-4].type == 'and':
                lexical_array = supplement_relation_for_instance(lexical.std_name, lexical_array)
                return lexical_array
        else:
            return lexical_array
    else:
        return lexical_array


# 去掉停用词
def remove_stopwords(seq_que):
    stop_words_list = ['为', '了', '的', '在', '之间', '且', '中', '做', '做了']
    seq_stopwords = []
    for word in seq_que:
        if word in stop_words_list:
            seq_stopwords.append(word)
    for item in seq_stopwords:
        seq_que.remove(item)
    return seq_que


def word2type(seq_que):
    lexical_array = []
    print('########### 开始实体链接 ###########')
    seq_que = remove_stopwords(seq_que)
    statistics_word = ['平均', '最大', '最小']  # 前置统计词后置预处理
    for i in range(len(seq_que)):
        for x in statistics_word:
            index = seq_que[i].find(x)
            if index != -1 and seq_que[i] != x:
                seq_que.insert(i, seq_que[i][index+2:len(seq_que[i])])
                seq_que.insert(i, x)
                del seq_que[i + 2]

    # 识别Concept: 病人/医嘱详情/手术详情/化验详情/疾病详情
    for index, word in enumerate(seq_que):
        transfer_flag = 0       # 单词识别完成标识
        lexical = identify_concept(index=index, word=word)
        if lexical != -1:
            lexical_array.append(lexical)
            transfer_flag = 1

        # 识别Property: propertyS propertyN propertyD
        # 词典key_set: propertyX.Concept
        if transfer_flag == 0:
            lexical = identify_property(index=index, word=word)
            if lexical != -1:
                # 二义性消歧
                if lexical.name in ['住院', "入院", "出院"]:
                    if len(lexical_array) > 2 and lexical_array[-1].type == 'rightSquareBracket':
                        if len(lexical_array) > 3 and lexical_array[len(lexical_array)-4].type == 'separator':
                            lexical_array.insert(len(lexical_array)-7, lexical)
                            transfer_flag = 1
                        else:
                            lexical_array.insert(len(lexical_array)-3, lexical)
                            transfer_flag = 1
                else:
                    lexical_array.append(lexical)
                    transfer_flag = 1

        # 识别Relation: Concept Relation Concept
        # key: concept.concept
        if transfer_flag == 0:
            lexical = identify_relation(index=index, word=word)
            if lexical != -1:
                lexical_array.append(lexical)
                supplement_instance_for_relation(index=index, lexical=lexical, seq_que=seq_que, lexical_array=lexical_array)
                transfer_flag = 1

        # 识别Instance
        # key: relation.concept
        if transfer_flag == 0:
            lexical = identify_instance(index=index, word=word, lexical_array=lexical_array, seq_que=seq_que)
            if lexical != -1:
                lexical_array.append(lexical)
                transfer_flag = 1

        # 识别atom
        if transfer_flag == 0:
            lexical = identify_atom(index=index, word=word, lexical_array=lexical_array)
            if lexical != -1:
                lexical_array.append(lexical)
                transfer_flag = 1

        # 识别number_value
        if transfer_flag == 0:
            lexical = identify_number_value(index=index, word=word)
            if lexical != -1:
                lexical_array.append(lexical)
                transfer_flag = 1
        if transfer_flag == 0:
            lexical = identify_datetime_value(index=index, word=word)
            if lexical != -1:
                lexical_array.append(lexical)
                transfer_flag = 1
        if transfer_flag == 0:
            if word == '[':
                lexical = LexiconEntry(name=word, std_name=word, type='leftSquareBracket', belong='atom', index=index)
                lexical_array.append(lexical)
                transfer_flag = 1
                print_lexical(lexical)
            elif word == ']':
                lexical = LexiconEntry(name=word, std_name=word, type='rightSquareBracket', belong='atom', index=index)
                lexical_array.append(lexical)
                transfer_flag = 1
                print_lexical(lexical)
            # 识别string_value 如果单词类型不属于class、instance、relation、property、number_value、value_data
            # 处理非标准简称字符串值，如“女性、性别为女”

        if transfer_flag == 0:
            lexical = identify_string_value(index=index, word=word, lexical_array=lexical_array)
            if lexical != -1:
                lexical_array.append(lexical)
                transfer_flag = 1

        if transfer_flag == 0:
            lexical = identify_statistics(index=index, word=word, lexical_array=lexical_array)
            if lexical != -1:
                lexical_array.append(lexical)
                transfer_flag = 1

        # 未识别词
        if transfer_flag == 0:
            lexical = LexiconEntry(name=word, std_name=word, type='unknown', belong='unknown', index=index)
            #lexical_array.append(lexical)
            print_lexical(lexical)
        if index == len(seq_que)-1:
            last_lexical = lexical_array[-1]
            if len(lexical_array) > 1:
                second_last_lexical = lexical_array[len(lexical_array)-2]
                if last_lexical.type in ['concept', 'propertyN', 'propertyS']:
                    if second_last_lexical.belong == 'statistics':
                        pass
                    else:
                        last_lexical = LexiconEntry(name='列表', std_name='列表', type='list', belong=last_lexical.std_name,
                                                    index=index + 1)
                        lexical_array.append(last_lexical)
                        print_lexical(last_lexical)
            else:
                if last_lexical.type in ['concept', 'propertyN', 'propertyS']:
                    last_lexical = LexiconEntry(name='列表', std_name='列表', type='list', belong=last_lexical.std_name, index=index+1)
                    lexical_array.append(last_lexical)
                    print_lexical(last_lexical)
    return lexical_array


def print_lexical(lexical):
    print(str(lexical.index) + ',' + lexical.name + ',' + lexical.std_name + ',' + lexical.type + "," + lexical.belong)
