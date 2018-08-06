#-*- coding: cp936 -*-
import os, codecs, sys
from operator import itemgetter
from datetime import datetime
from datetime import timedelta
import pandas as pd

INDEX_NUMBER = 0

intention_map = {'car:unknown:def':'���ض�','auto_only:nav:def':'������ָ���ص�','auto_only:ude:na':'�������޵����ؼ��ʣ�','car:dial:contact':'��绰����ϵ��','thirdparty:def':'������','mediamusic:play:song':'����ָ���������в��Źؼ��ʣ�','mediamusic:play':'��������ָ��','mediamusic:na:song':'����ָ���������޲��Źؼ��ʣ�','mediamusic:play:radiostation':'����ָ����̨','radio:off':'�رյ�̨','cmd:cancel':'ȡ��ָ��','weather:lookup':'������ѯ','auto_only:localsearch:def':'��������','mediamusic:na':'����ָ��','open:app':'��App','contact:lookup':'��ϵ�˲�ѯ','mediamusic:search:song':'��������','mediamusic:na:artist':'����ָ�����������֣��޲��Źؼ��ʣ�','mediamusic:play:artist':'����ָ������������','auto_only:map:def':'�򿪵�ͼ','mediamusic:na:album':'����ָ��ר�����޲��Źؼ��ʣ�','mediamusic:play:album':'����ָ��ר�����в��Źؼ��ʣ�'}

pattern_map = {'locality + fulllocation':'POI','fulllocation + street + buildingnum':'�ֵ� + ���ƺ�','street + fulllocation':'��·','fulllocation + street':'�ֵ�','fulllocation + street + intersectingstreet':'����·','locality + fulllocation + city':'���� + ����','fulllocation + locality + city':'����+ POI','locality + fulllocation + name':'  POI + ����','fulllocation + locality + name':'���� + POI','locality + fulllocation + cat':'���� + POI����','name + cat':'����','fulllocation + locality + cat':'POI���� + ����','locref + cat':'����+ POI����','locality + fulllocation + city + name':'���� + ���� + POI','fulllocation + locality + city + name':'����+����+ POI','name + locality + fulllocation':'POI + ����','fulllocation + street + intersectingstreet + trafficcategory':'�����','name + fulllocation + locality':'���� + POI','city + fulllocation + locality + name':'����+��·+POI','city + locality + fulllocation + name':'POI +��·+����','city + fulllocation + locality':'POI+��·','city + locality + fulllocation':'���� + ����','fulllocation + city + locality + cat':'���� + POI����','fulllocation + city + locality + name':'POI +��·+����','fulllocation + city + locality + street':'���� + ���� + ��·','fulllocation + locality':'POI','fulllocation + locality + buildingnum':'POI + ���ƺ�','fulllocation + locality + state + city':'ʡ + ���� + POI + ����','fulllocation + locality + street':'POI + ��·','fulllocation + street + cat':'���� + ��·','locref + name':'����+ POI','street + fulllocation + cat':'����+��·','street + fulllocation + name':'��· + POI','text + cat_implicit':'��Ҫ��Ϣ�������Ҷ��ˣ�'}

domain_map = {'auto_only':'����','car':'���ض�','mediamusic':'����','thirdparty':'������','radio':'������','cmd':'����'}

def get_time_stats (cols, time_stats):
    time = cols[1]
    hour = time.split(':')[0]
    if hour not in time_stats:
        time_stats[hour] = 1
    else:
        time_stats[hour] += 1
    return time_stats

def get_date_stats(cols, date_stats):
    date = cols[0]
    if date not in date_stats:
        date_stats[date] = 1
    else:
        date_stats[date] += 1
    return date_stats

def get_date_user_stats(cols, date_user_stats, user_list, index):
    date = cols[0]
    user = cols[5]
       
    if date not in date_user_stats:
        global INDEX_NUMBER
        index[date] = INDEX_NUMBER
        print(INDEX_NUMBER)
        INDEX_NUMBER += 1
        date_list = []
        user_list.append(date_list)
        date_user_stats[date] = 1
        if user not in user_list[index[date]]:
            user_list[index[date]].append(user)
    else:
        if user not in user_list[index[date]]:
            user_list[index[date]].append(user)
            date_user_stats[date] += 1

    return date_user_stats, user_list

def get_asr_stats (cols, asr_stats):
    try:
        asr = cols[2]
        if asr != '':
            if asr not in asr_stats:
                asr_stats[asr] = 1
            else:
                asr_stats[asr] += 1
    except:
        pass
    return asr_stats

def get_intention_stats (cols, intention_stats):
    parseType = cols[3]
    if parseType != '':
        if parseType in intention_map:
            if intention_map[parseType] not in intention_stats:
                intention_stats[intention_map[parseType]] =  1
            else:
                intention_stats[intention_map[parseType]] +=  1
        else:
            if parseType not in intention_stats:
                intention_stats[parseType] =  1
            else:
                intention_stats[parseType] +=  1
    return intention_stats

def get_domain_stats (cols, domain_stats):
    parseType = cols[3]
    if parseType != '':
        domain = parseType.split(':')[0]
        if domain in domain_map:
            if domain_map[domain] not in domain_stats:
                domain_stats[domain_map[domain]] = 1
            else:
                domain_stats[domain_map[domain]] += 1
        else:
            if domain not in domain_stats:
                domain_stats[domain] = 1
            else:
                domain_stats[domain] += 1
    return domain_stats

def get_user_stats (cols, user_stats):
    user = cols[5]
    if user not in user_stats:
        user_stats[user] = 1
    else:
        user_stats[user] += 1
    return user_stats

def get_user_feedback (cols, feedback_stats):
    options = [u'��һ��', u'һ', u'�ڶ���', u'��', u'������', u'��', u'���ĸ�']
    negate = [u'����', u'û��', u'����']
    confirm = [u'�ǵ�', u'��', u'��', u'ȷ��']
    try:
        asr = cols[2]
        if asr in options:
            feedback_stats['choose'] += 1
        elif asr in negate:
            feedback_stats['negate'] += 1
        elif asr in confirm:
            feedback_stats['confirm'] += 1
    except:
        pass
    return feedback_stats

def get_open_close_command (cols, cmd_stats, cmd_string):
  
    close_cmd = [u"�ر�", u"����", u"�ص�", u"����", u"ȡ��"]
    open_cmd = [u'����', u"��ʼ", u"����", u"����", u"��", u"����", u"����"]
    try:
        ans = cols[2]
        if cmd_string == 'open' and ans != '': 
            secondfilter = False
            for keys in open_cmd:
                if ans.startswith(keys):
                    target = ans.replace(keys, '') 
                    secondfilter = True
                    if target not in cmd_stats and target != '':
                        cmd_stats[target] = 1
                    else:
                        cmd_stats[target] += 1
                if ans.startswith(u'��') and secondfilter == False:
                    target = ans.replace(u'��', '')
                    if target not in cmd_stats:
                        cmd_stats[target] = 1
                    else:
                        cmd_stats[target] += 1
                        
        elif cmd_string == 'close' and ans != '':
            second_filer = False
            for keys in close_cmd:
                if ans.startswith(keys):
                    target = ans.replace(keys, '')
                    secondfilter = True
                    if target not in cmd_stats and target != '':
                        cmd_stats[target] = 1
                    else:
                        cmd_stats[target] += 1
                if ans.startswith(u'��') and secondfilter == False:
                    target = ans.replace(u'��', '')
                    if target not in cmd_stats:
                        cmd_stats[target] = 1
                    else:
                        cmd_stats[target] += 1
    except:
        pass
    return cmd_stats

def output_eNLU (cols, outname):
    fout = codecs.open(outname, 'a', 'utf8')
    parseType = cols[3]
    try:
        ans = cols[2]
        if '' in ans:
            ans = ans.replace('', '')
        if parseType == 'car:unknown:def' and ans != '':
            sent = ans + '#res_type_NCS#DB.OtherTopic' + '\n'
            fout.write(sent)
    except:
        pass
    fout.close()


def count_popular_slot (cols, intended_domain, intended_slotname, slot_name_stats):
    domain = cols[3].split(':')[0]
    mentionList = cols[4]
    if domain == intended_domain and mentionList != '':
        splits = mentionList.split("|")
        for slot in splits:
            if slot.startswith(intended_slotname):
                value = slot.split("=")[1].split("(")[0]
                if value not in slot_name_stats:
                    slot_name_stats[value] = 1
                else:
                    slot_name_stats[value] += 1
    return slot_name_stats


def get_slot_pattern_stats (cols, intended_domain, slot_pattern_stats):
    domain = cols[3].split(':')[0]
    if domain == intended_domain:
        mentionList = cols[4]
        slots = mentionList.split('|')
        if len(slots) > 1:
            slot_name = [slot.split('=')[0] for slot in slots]
            pattern = ' + '.join(slot_name)
            if pattern in pattern_map:
                if pattern_map[pattern] not in slot_pattern_stats:
                    slot_pattern_stats[pattern_map[pattern]] = 1
                else:
                    slot_pattern_stats[pattern_map[pattern]] += 1
            else:
                if pattern not in slot_pattern_stats:
                    slot_pattern_stats[pattern] = 1
                else:
                    slot_pattern_stats[pattern] += 1
    return slot_pattern_stats

def sorted_dic_to_excel (dic, writer, threshold, col_1_nm, col_2_name, sheetname):
    row = []
    value = []
    for i in range(threshold):
        row.append(dic[i][0])
        value.append(dic[i][1])
    df = pd.DataFrame({col_1_nm: row, col_2_name: value})
    df.to_excel(writer, sheetname)

def dic_to_excel (dic, writer, col_1_nm, col_2_name, sheetname):
    row = []
    value = []
    for i in dic:
        row.append(i)
        value.append(dic[i])
    df = pd.DataFrame({col_1_nm: row, col_2_name: value})
    df.to_excel(writer, sheetname)

def get_successful_rate (cols, adic):
    date = cols[0]
    asr = cols[2]
    if date not in adic:
        adic[date] = {'suc':0, 'unsuc':0}
        if asr == '':
            adic[date]['unsuc'] += 1
        else:
            adic[date]['suc'] += 1
    else:
        if asr == '':
            adic[date]['unsuc'] += 1
        else:
            adic[date]['suc'] += 1
    return adic

def success_rate_to_excel (adic, writer, col_1_nm, col_2_nm, col_3_nm, sheetname):
    days = []
    suc = []
    unsuc = []
    for day in adic:
        days.append(day)
        suc.append(adic[day]['suc'])
        unsuc.append(adic[day]['unsuc'])
    df = pd.DataFrame({col_1_nm: days, col_2_nm: suc, col_3_nm:unsuc})
    df.to_excel(writer, sheetname)

def main (infile):

    tsv = infile[:-4] + "_temp.tsv" 
#    tsv = infile
    eNLU = infile[:-4] + "_eNLU.txt"
    excel = infile[:-4] + '.xlsx'

    print ('Finished converting raw log to temporary log.')
    
    fin = codecs.open(tsv, 'r', 'utf8')
    lines = fin.readlines()

    time_stats = {}
    date_stats = {}
    user_list = []
    index = {}
    date_user_stats = {}
    asr_stats = {}
    intention_stats = {}
    domain_stats = {}
    user_stats = {}
    feedback_stats = {'choose':0, 'negate':0, 'confirm':0}
    success_rate = {}
    open_stats = {}
    close_stats = {}
    slot_name_stats = {}
    slot_cat_stats = {}
    slot_street_stats = {}
    slot_locality_stats = {}
    slot_artist_stats = {}
    slot_song_stats = {}
    slot_genre_stats = {}
    pattern_stats = {}
    writer = pd.ExcelWriter(excel)

    for line in lines[1:-1]:
        cols = line.split("\t")
        success_rate = get_successful_rate (cols, success_rate)
        time_stats = get_time_stats (cols, time_stats)
        date_stats = get_date_stats(cols, date_stats)
        date_user_stats, user_list = get_date_user_stats(cols, date_user_stats, user_list, index)		
        domain_stats = get_domain_stats (cols, domain_stats)
        pattern_stats = get_slot_pattern_stats (cols, 'auto_only', pattern_stats)
        user_stats = get_user_stats (cols, user_stats)
        asr_stats = get_asr_stats (cols, asr_stats)
        intention_stats = get_intention_stats (cols, intention_stats)
        feedback_stats = get_user_feedback (cols, feedback_stats)
        open_stats = get_open_close_command (cols, open_stats, 'open')
        close_stats = get_open_close_command (cols, close_stats, 'close')

        slot_name_stats = count_popular_slot (cols, 'auto_only', 'name', slot_name_stats)
        slot_cat_stats = count_popular_slot (cols, 'auto_only', 'cat', slot_cat_stats)
        slot_street_stats = count_popular_slot (cols, 'auto_only', 'street', slot_street_stats)
        slot_locality_stats = count_popular_slot (cols, 'auto_only', 'locality', slot_locality_stats)
        slot_artist_stats = count_popular_slot (cols, 'mediamusic', 'artist', slot_artist_stats)
        slot_song_stats = count_popular_slot (cols, 'mediamusic', 'song', slot_song_stats)
        slot_genre_stats = count_popular_slot (cols, 'mediamusic', 'genre', slot_genre_stats)

        output_eNLU (cols, eNLU)

    print ('Finish collecting statistics.')
    
    #sort some dictionaries
    sorted_asr_stats = sorted(asr_stats.items(), key=itemgetter(1), reverse=True)
    sorted_pattern_stats = sorted(pattern_stats.items(), key=itemgetter(1), reverse=True)
    sorted_user_stats = sorted(user_stats.items(), key=itemgetter(1), reverse=True)
    sorted_intention_stats = sorted(intention_stats.items(), key=itemgetter(1), reverse=True)
    sorted_open_stats = sorted(open_stats.items(), key=itemgetter(1), reverse=True)
    sorted_close_stats = sorted(close_stats.items(), key=itemgetter(1), reverse=True)

    sorted_slot_name_stats = sorted(slot_name_stats.items(), key=itemgetter(1), reverse=True)
    sorted_slot_cat_stats = sorted(slot_cat_stats.items(), key=itemgetter(1), reverse=True)
    sorted_slot_street_stats = sorted(slot_street_stats.items(), key=itemgetter(1), reverse=True)
    sorted_slot_locality_stats = sorted(slot_locality_stats.items(), key=itemgetter(1), reverse=True)
    sorted_slot_artist_stats = sorted(slot_artist_stats.items(), key=itemgetter(1), reverse=True)
    sorted_slot_song_stats = sorted(slot_song_stats.items(), key=itemgetter(1), reverse=True)
    sorted_slot_genre_stats = sorted(slot_genre_stats.items(), key=itemgetter(1), reverse=True)


    #output normal dictionaries
    dic_to_excel (time_stats, writer, 'Hour', 'count', 'time')
    dic_to_excel (date_stats, writer, 'Date', 'count', 'date')
    dic_to_excel (date_user_stats, writer, 'Date', 'user count', 'dateUser')
    dic_to_excel (domain_stats, writer, 'Domain', 'count', 'domain')
    dic_to_excel (feedback_stats, writer, 'Feedback', 'count', 'feedback')
    success_rate_to_excel (success_rate, writer, 'Day', 'Suc', 'Unsuc', 'sucRate')
	
	#output sorted arrays of dictionaries
    sorted_dic_to_excel (sorted_asr_stats, writer, 100, 'ASR', 'count', 'topASR')
    sorted_dic_to_excel (sorted_pattern_stats, writer, 100, 'Pattern', 'count', 'pattern')
    sorted_dic_to_excel (sorted_user_stats, writer, 1, 'UserID', 'count', 'user')
    sorted_dic_to_excel (sorted_intention_stats, writer, 20, 'Intention', 'count', 'intention')
    sorted_dic_to_excel (sorted_open_stats, writer,  50, 'OpenCMD', 'count', 'openCMD')
    sorted_dic_to_excel (sorted_close_stats, writer, 50, 'CloseCMD', 'count', 'closeCMD')

    #output slots
    sorted_dic_to_excel (sorted_slot_name_stats, writer, 50, 'Slot:Name', 'count', 'slot_name')
    sorted_dic_to_excel (sorted_slot_cat_stats, writer, 50, 'Slot:Cat', 'count', 'slot_cat')
    sorted_dic_to_excel (sorted_slot_street_stats, writer, 50, 'Slot:Street', 'count', 'slot_street')
    sorted_dic_to_excel (sorted_slot_locality_stats, writer, 50, 'Slot:Locality', 'count', 'slot_locality')
    sorted_dic_to_excel (sorted_slot_artist_stats, writer, 20, 'Slot:Artist', 'count', 'slot_artist')
    sorted_dic_to_excel (sorted_slot_song_stats, writer, 20, 'Slot:Song', 'count', 'slot_song')
    sorted_dic_to_excel (sorted_slot_genre_stats, writer, 20, 'Slot:Genre', 'count', 'slot_genre')

   

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print ("error: please input python Log2Excel.py file.tsv")
		exit()
	infile = sys.argv[1]
	main (infile)
