import jieba
from qa import LexiconModel
from qa import GrammarParser
from qa import CypherBuilder
import re
import os
from neo4j.v1 import GraphDatabase, basic_auth, Node
#import logging
#logging.basicConfig(filename='info.log', level=logging.DEBUG)
"""对question进行预处理
1: 非标准时间(2017年1月11日) --> 标准时间格式(201701011)
2:
"""

def preprocess(question):
    print('预处理前:' + question)
    question = question.strip(' ')
    datetime_pattern = re.compile('(([12][0-9]{3})[年|/|\-|\.]?([01]?[0-9](?=\D))?[月|/|\-|\.]?([0-3]?[0-9](?=\D))?[日|号]?)')
    tuples = datetime_pattern.findall(question)
    for i in range(len(tuples)):
        date = ''
        for j in range(len(tuples[i])):
            if j == 0:
                continue
            # 月日，如果是0-9，补0.例如，9-》09
            if (j == 2 or j == 3) and len(tuples[i][j]) == 1:
                date = date + ('0' + tuples[i][j])
            # 如果月日为空，补00
            elif len(tuples[i][j]) == 0:
                date = date + '00'
            else:
                date = date + tuples[i][j]
        date = '[' + date + ']'
        question = question.replace(tuples[i][0], date)
    print('预处理后:' + question)
    return question

dir_name = os.path.dirname(__file__)
jieba.load_userdict(os.path.join(dir_name, 'dict/custom.dic'))

uri = "bolt://172.20.46.92:7687/"
driver = GraphDatabase.driver(uri, auth=basic_auth("neo4j", "admin"))

def word_segmentation(question):
    pre_que = preprocess(question)
    seq_que = list(jieba.cut(pre_que))
    print('结巴分词结果:' + ', '.join(seq_que))
    return seq_que


def parsing(question):
    print("《输入问题》" + question)
    seq_que = word_segmentation(question)
    lexical_array = LexiconModel.word2type(seq_que)
    select_tuples_list, condition_children = GrammarParser.grammar_parsing(lexical_array)
    cypher, question_type = CypherBuilder.build(select_tuples_list, condition_children)
    result = neo4j_execute(cypher)
    lexical_seq = []
    question_type_tuple = (-1, -1)
    for x in lexical_array:
        lexical_seq.append(x.name)
    for item in question_type.items():
        if item[1] != -1:
            question_type_tuple = item
    return result, lexical_seq, question_type_tuple


def neo4j_execute(query):
    with driver.session() as session:
        with session.begin_transaction() as tx:
            result = []
            for record in tx.run(query):
                record_value = record['final_result']
                if isinstance(record_value, Node):
                    result.append(record_value.properties)
                else:
                    result.append(record_value)

            print(result)
            return result


if __name__ == "__main__":
    question = "患有肺癌或气血亏虚证的患者的最大年龄?"
    #question = "总共有多少患者？"
    #question = '患有肺癌或气血亏虚证的患者的平均住院次数?'
    #question = '2013年入院的患者?'
    #question = '患有肺癌和气血亏虚证的患者手术分布?'
    #question = "60-90岁的女性患者"
    #question = "年龄为60-90岁的冠心病患者"
    #question = "血红蛋白浓度偏低的女性患者用药分布"
    #question = "甲亢患者"
    #question = "2014年之后患有冠心病或者被诊断为肺癌的患者"
    #question = " 没有做过盆腔占位微波消融术和经皮腹腔穿刺术患者的用药分布"
    #question = " 患有溃疡性结肠炎患者的平均年龄"
    #question = " 诊断出甲状腺功能亢进症或溃疡型结肠炎患者的平均年龄"
    #question = " 住院次数最多的冠心病患者" ？？？
    #question = " 年纪最大的女性患者" ？？？
    #question = " 出院日期在2013至2014年的患者的平均住院次数"
    #question = " 入院时间在2013年7月至2014年1月的患者的平均住院次数"
    #question = " 2013至2014年期间出院的患者的平均住院次数"
    # question = " 在2012至2014年期间做了骨髓活检术且采用局部麻醉的患者的用药分布" $%$#@!$@!%@^T#$^%#&$
    #question = " 60-90岁的肝阳上亢证患者"
    #question = " 1970年之后患有冠心病的患者年龄分布"
    #question = " 入院时间为2013年10月9日的患者"
    #question = " 2013年10月9日入院的患者"
    #question = " 大于30岁小于60岁患有冠心病的患者数量"
    #question = " 住院超过60天的患者的平均年龄" ？？？？？？？？？
    #question = " 2013年10月9日至2013年12月9日出院的患者"
    #question = "50-80岁做过肠镜下肠活检术的直肠癌女性患者总数"
    #question = " 2014年以前没有做过超声引导下肝脏肿瘤射频消融术或腹腔注射术且心律失常和白内障的患者的用药分布"
    #question = " 2013-2014年期间服用了至灵胶囊或白玉膏的A型血患者的住院次数分布"
    #question = " 2013年患有冠心病或者肺癌且服用了至灵胶囊的女性患者的平均年龄"
    #question = " 2013年之后服用了至灵胶囊或者使用了白玉膏或者使用了艾迪注射液的男性肺癌患者的年龄分布"
    #question = " 2012年9月至2014年1月诊断出肺癌且期间住院次数在3-5次的女性患者的用药分布"
    #question = " 60-90岁服用了艾迪注射液或者服用了至灵胶囊和艾迪注射液的患者的性别分布"
    #question = " 没有做过超声引导下肝脏肿瘤射频消融术或者没有做过腹腔注射术的女性肺癌患者的用药分布"
    #question = "60-90岁男性患者的年龄分布"
    #question = "患者吃了哪些药"
    #question = "患有肺癌或冠心病并且服用了硝酸异山梨酯和欣康的女性患者?"
    #question = '冠心病患者中患有冠心病的年龄分布'
    #question = '肺癌患者中年纪最大的患者' ？？？？？？？？
    #question = '住院次数大于4次的肺癌患者做了哪些手术?'
    #question = '患有气血亏虚证的男性肺癌患者'
    #question = '肺癌患者中年纪最大的' ？？？
    question = '艾迪注射液的代码是多少？'
    question = '利尿剂包含哪些药？'
    #question = '患者的用药分布'
    #question = '60-90岁女性心衰患者中服用平消片和百令胶囊或服用六味地黄丸和金水宝胶囊的患者手术分布'
    #question = '2012-2013年期间冠心病入院的患者数量？'
    #question = '有哪些化验？'
    #question = '天门冬氨酸转移氨酶的参考值是多少？'
    parsing(question)


