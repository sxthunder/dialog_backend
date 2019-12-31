# coding:utf-8
from nltk import CFG
import nltk.tree
import os
#import logging
#logging.basicConfig(filename='info.log', level=logging.DEBUG)
"""
文法解析层
"""


class GrammarParser(object):

    def __init__(self, grammar):
        self.grammar = CFG.fromstring(grammar)
        self.parser = nltk.ChartParser(self.grammar)
        self.words_list = []

    def parse(self, words_list):
        return self.parser.parse(words_list)


def preprocess(lexical_array):
    print('########### 开始语法分析预处理 ###########')
    lexical_array_temp = lexical_array
    word_list = []
    type_list = []
    unknown_list = []
    for x in range(len(lexical_array_temp)-1):
        lexical_array_temp[x].index = x
    for item in lexical_array_temp:
        if item.type == 'unknown':
            print_lexical(item)
            unknown_list.append(item)
        else:
            word_list.append(item.std_name)
            type_list.append(item.type)
    for unknown in unknown_list:
        lexical_array.remove(unknown)
    print('单词序列:', ', '.join(word_list))
    print('类型序列:', ', '.join(type_list))
    return lexical_array, type_list


def is_valid_tree(tuples_list):
    dist_seq_rp = []
    dist_seq = []
    dist_seq_label = []
    for quintuple in tuples_list:
        if len(quintuple) == 4:
            if quintuple[3] == 'RelationPropertyCondition':
                if quintuple[2] in ['propertyN', 'instance', 'concept', 'propertyS']:
                    dist_seq_rp.append(quintuple[1])
            elif quintuple[3] in ['RelationCondition', 'PropertyCondition']:
                if quintuple[2] in ['propertyN', 'instance', 'concept', 'propertyS']:
                    dist_seq.append(quintuple[1])
                    dist_seq_label.append(quintuple[3])
            else:
                continue
    if len(dist_seq_rp) > 0:
        flag = 0
        for x in dist_seq_rp:
            if dist_seq_rp[0] != x:
                flag = 1
                break
        if flag == 0:
            return True
        else:
            return False
    else:
        flag = 0
        if len(dist_seq) > 0:
            temp = dist_seq[0]
            temp_label = dist_seq_label[0]
            for x in range(1, len(dist_seq)):
                if temp_label == dist_seq_label[x]:
                    temp_label = dist_seq_label[x]
                    temp = dist_seq[x]
                    continue
                if temp == dist_seq[x]:
                    flag = 1
                    break
                else:
                    temp_label = dist_seq_label[x]
                    temp = dist_seq[x]
            if flag == 0:
                return True
            else:
                return False
        else:
            return True


def grammar_parsing(lexical_array):
    dir_name = os.path.dirname(__file__)
    typed_word_list, type_list = preprocess(lexical_array)
    fp = open(os.path.join(dir_name, 'grammar'), encoding='utf-8')
    try:
        grammar = fp.read().strip('\n')
    finally:
        fp.close()
    grammar_parser = GrammarParser(grammar)
    trees = grammar_parser.parse(type_list)
    select_tuples_list = []
    condition_children = []
    selected_tree = ''
    # 遍历每棵树
    for tree in trees:
        condition_subtrees = tree.subtrees(lambda t: t.label() == 'Condition')
        s_subtree = list(tree.subtrees(lambda t: t.label() == 'Statistics'))
        t_conditons = list(tree.subtrees(lambda t: t.label() == 'TimeBlock'))
        rp_conditons = list(tree.subtrees(lambda t: t.label() == 'RelationPropertyCondition'))
        r_conditons = list(tree.subtrees(lambda t: t.label() == 'RelationCondition'))
        p_conditons = list(tree.subtrees(lambda t: t.label() == 'PropertyCondition'))
        direction = list(tree.subtrees(lambda t: t.label() == 'Direction'))
        condition_children = []
        for cond in condition_subtrees:
            for child in cond:
                if type(child) is str:
                    condition_children.append(child)
                elif child.label() == 'Condition':
                    pass
                else:
                    condition_children.append(child.label())
        t_counter = r_counter = p_counter = d_counter = s_counter = rp_counter = 0
        leaves = []
        for index, item in enumerate(condition_children):
            if item == 'TimeBlock':
                leaves.append(t_conditons[t_counter].leaves())
                t_counter += 1
            elif item == 'RelationPropertyCondition':
                leaves.append(rp_conditons[rp_counter].leaves())
                rp_counter += 1
                p_counter += 1
                r_counter += 1
            elif item == 'RelationCondition':
                leaves.append(r_conditons[r_counter].leaves())
                r_counter += 1
            elif item == 'PropertyCondition':
                leaves.append(p_conditons[p_counter].leaves())
                p_counter += 1
            elif item == 'Direction':
                leaves.append(direction[d_counter].leaves())
                d_counter += 1
            elif item == 'Statistics':
                leaves.append(s_subtree[s_counter].leaves())
                s_counter += 1
            else:
                leaves.append(item)
        lexical_tuple_list = []
        temp_tuple_list = []
        counter = 0
        for index, x in enumerate(leaves):
            if type(x) is list:
                temp = []
                for y in x:
                    temp.append((lexical_array[counter].std_name, lexical_array[counter].belong,
                                 lexical_array[counter].type, condition_children[index]))
                    temp_tuple_list.append((lexical_array[counter].std_name, lexical_array[counter].belong,
                                            lexical_array[counter].type, condition_children[index]))
                    counter += 1
                lexical_tuple_list.append(temp)
            else:
                temp_tuple_list.append((lexical_array[counter].std_name, lexical_array[counter].belong,
                                        lexical_array[counter].type, condition_children[index]))
                lexical_tuple_list.append((lexical_array[counter].std_name, lexical_array[counter].belong,
                                           lexical_array[counter].type, condition_children[index]))
                counter += 1
        if is_valid_tree(temp_tuple_list):
            select_tuples_list = lexical_tuple_list
            selected_tree = tree
            print('########### 非终结符序列 ###########')
            print(",".join(condition_children))
            break
        else:
            continue
    print('########### 语法树 ###########')
    if type(selected_tree) != str:
        selected_tree.pprint()
        #selected_tree.draw()
    else:
        print(selected_tree)
    print("############# 语法结构 #############")
    for item in select_tuples_list:
        print(item)
    return select_tuples_list, condition_children


def print_lexical(lexical):
    print(str(lexical.index) + ',' + lexical.name + ',' + lexical.std_name + ',' + lexical.type + "," + lexical.belong)
