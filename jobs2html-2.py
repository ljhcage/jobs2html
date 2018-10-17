# coding=utf-8
from __future__ import division
from __future__ import unicode_literals
import time
import urllib2
import urllib
import re
from bs4 import BeautifulSoup
#import BeautifulSoup
from json import loads
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

header = {'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'}

# 存放信息的类定义
class infor(object):
    def __init__(self, company, ttime, strtime, addr, url):
        self.company = company
        self.ttime = ttime
        self.strtime = strtime
        self.addr = addr
        self.surl = url
    def __eq__(self, other):
        if(self.company==other.company)and(self.ttime==other.ttime):return True

# 定义去重类
class addrtime(object):
    def __init__(self, ttime, addr):
        self.time = ttime
        self.addr = addr
    def __eq__(self, other):
        if(self.addr==other.addr)and(self.time == other.time):return True

# 抓取本科招聘信息
def getUlist(url, output, handle, inforL, urllist):
    reg = urllib2.Request(url, None, header)
    urlcontent = urllib2.urlopen(reg).read()  # .decode("gbk").encode('utf-8')
    soup = BeautifulSoup(urlcontent, "html.parser")
    # if (soup.find_all("fdhy_tb002"
    target = soup.select(".fdhy_tb002")[1].contents
    pattern = re.compile('下一页</a>')
    for i in range(3, target.__len__(), 2):  # 循环每一个宣讲会
        temp = target[i].contents
        if (temp[1].__len__() >= 5):#出现医科的情况的话进入这个分支
            company = "[" + temp[1].contents[1].contents[0] + "]" + temp[1].contents[3].contents[0].encode(
                "utf-8").decode("utf-8")
            if (re.match('http', temp[1].contents[1].attrs["href"])):
                surl = temp[1].contents[3].attrs["href"]
            else:
                surl = "http://job.hust.edu.cn" + temp[1].contents[3].attrs["href"]
        else:#没有医科时的常规分支
            company = temp[1].contents[1].contents[0].encode("utf-8").decode("utf-8")
            if (re.match('http', temp[1].contents[1].attrs["href"])):
                surl = temp[1].contents[1].attrs["href"]
            else:
                surl = "http://job.hust.edu.cn" + temp[1].contents[1].attrs["href"]
        ttime = time.strptime(temp[3].contents[0].contents[0], "%Y-%m-%d %H:%M ")
        strtime = time.strftime('%m月%d日 %H:%M'.encode('utf-8'), ttime).decode("utf-8")
        addr = temp[5].contents[0].contents[0]
        re.sub("（华科）| ", "", addr)
        # print ("%s\t%s\t%s\t%s" %(company,ttime,addr,surl))
        #strtemp = company + "\n" + strtime + "\n" + addr + "\n详情见：" + surl + "\n\n"
        tempinfor = infor(company, ttime, strtime, addr, surl)
        urllist.append(surl)
        inforL.append(tempinfor)
        #output = strtemp + output
    match = pattern.findall(unicode(str(soup), "utf8"))
    if (match.__len__() > 0):
        try:
            (inforL,urllist) = getUlist("http://job.hust.edu.cn/" + soup.select(".pagination")[0].contents[-4].attrs["href"], output,handle, inforL, urllist)  # 递归调用
        except IndexError:
            (inforL, urllist) = getUlist("http://job.hust.edu.cn/" + soup.select(".pagination")[0].contents[-2].contents[-4].attrs["href"], output, handle,inforL, urllist)
        # else:
        # print output
        # handle.write(output.encode("gbk"))
    return inforL, urllist

# 抓取岗位信息
def gethost(url):
    reg = urllib2.Request(url, None, header)
    urlcontent = urllib2.urlopen(reg).read()
    soup = BeautifulSoup(urlcontent, "html.parser")
    tablelist = soup.find_all('table')
    posi = ""
    if (tablelist.__len__()):
        for tab in tablelist:
            if (tab.contents.__len__() > 1):
                print "含有thead"
            else:  # 只有tbody，找到岗位信息所在的列数
                popattern = re.compile("岗位")
                poindex = 0
                rowlen = tab.contents[0].contents[0].contents.__len__()
                for td in tab.contents[0].contents[0].contents:
                    if (popattern.findall(td.text).__len__() == 0):
                        poindex += 1
                    else:
                        break
                for trindex in range(1, tab.contents[0].contents.__len__()):
                    if (tab.contents[0].contents[trindex].contents.__len__() == rowlen):
                        posi += (tab.contents[0].contents[trindex].contents[poindex].text + "，")
                    else:
                        continue
    return posi

# 研究生招聘信息抓取
def getMlist(inforL, daytime, daytime2, pagenum, urllist):
    param = urllib.urlencode({'queryModel.currentPage': str(pagenum), 'queryModel.showCount': '10',
                              'queryModel.sortName': 't1.sfyx, abs(t1.jlsj) ,t1.xjhkssj',
                              'queryModel.sortOrder': 'asc'})
    reg = urllib2.Request(
        'http://career.hust.edu.cn/zftal-web/zfjy!wzxx!hzkjdx10487/xjhxx_cxXjhForWeb.html?doType=query', None, header)
    reg.add_data(param)
    urlcontent = urllib2.urlopen(reg).read()
    dicts = loads(urlcontent)
    currentPage = dicts["currentPage"]
    totalPage = dicts["totalPage"]
    for item in dicts["items"]:
        try:
            ttime = time.strptime(re.sub(r'[^\x00-\x7F]+', '', item["xjhrq"] + ' ' + item["xjhkssj"]), '%Y-%m-%d %H:%M')
            # ttime = time.strptime(item["xjhrq"] + ' ' + item["xjhkssj"], '%Y-%m-%d %H:%M')  # 宣讲会日期+宣讲会开始时间
        except:
            ttime = time.strptime(re.sub('：', ':', item["xjhrq"] + ' ' + item["xjhkssj"]),
                                  '%Y-%m-%d %H:%M')  # 宣讲会日期+宣讲会开始时间
        if ((ttime < daytime) or (ttime > daytime2)): continue
        # elif(ttime>daytime2):continue
        surl = "http://career.hust.edu.cn/zftal-web/zfjy!wzxx/zfjy!wzxx!hzkjdx10487/xjhxx_ckXjhxx.html?sqbh=" + item[
            "sqbh"]
        if (surl in urllist):
            continue
        else:
            urllist.append(surl)
        addr = re.sub('华科研究生活动中心 ', '研究生活动中心', item["xjhcdmc"])  # 宣讲会场地名称
        pat1 = re.compile('（华科） ?')
        mat = pat1.findall(addr)
        addr = re.sub(pat1, "", addr)
        strtime = time.strftime('%m月%d日 %H:%M'.encode("utf-8"), ttime).decode("utf-8")
        reginner = urllib2.Request(surl, None, header)
        soup = BeautifulSoup(urllib2.urlopen(reginner).read(), "html.parser")
        comp = re.sub("校园宣讲会", "", soup.select("h3")[1].contents[1].text)
        comp = re.sub("宣讲会","",comp)
        tempinfor = infor(comp, ttime, strtime, addr, surl)
        if(tempinfor in inforL):continue
        inforL.append(tempinfor)
        # if(inforL[-1].ttime<daytime2):
    if (currentPage < totalPage - 10):
        getMlist(inforL, daytime, daytime2, currentPage + 1, urllist)
    return inforL

# 把list写到文件中
def writeFile(List, handle):
    for item in List:
        str = item.company + "\n" + item.strtime + "\n" + item.addr + "\n详情见：" + item.surl + "\n\n"
        handle.write(str.encode("gbk"))

# 招聘会信息的html代码拼接
def weekinfo2html(sortL):
    count = 1;
    htmltext = "<p style=\"line-height: 25.6px;white-space: normal;max-width: 100%;min-height: 1em;box-sizing: border-box !important;word-wrap: break-word !important;\"> <img src=\"http://mmbiz.qpic.cn/mmbiz_jpg/RW0pj7KFicIM2cn6MoBTaYC68esz4b8sRaDb4jz0Rv65dREib8rTq6ODcibPPgSVAv1wPxujykKLGaYjqmgqiceolg/640?wx_fmt=jpeg\" data-type=\"jpeg\" data-w=\"640\"f width=\"auto\" style=\"visibilityf: visible !important;width: auto !important;\"/><!--135不支持data-src的懒加载属性--></p>"
    for item in sortL:
        htmltext +="<!--招聘会信息，先是四个section包裹住公司名称--><section style=\"line-height:25.6px;white-space: normal;max-width: 100%;box-sizing: border-box;font-family: 微软雅黑;border-width: 0px;border-style: none;border-color: initial;word-wrap: break-word !important;\"><!--占据一整行的位置--><section style=\"margin: 10px auto;max-width: 100%;text-align: center;box-sizing: border-box !important;word-wrap: break-word !important;\"><!--把上下空间划分出来--><section style=\"margin: 10px auto;max-width: 100%;box-sizing: border-box;display: inline-block;word-wrap: break-word !important;\"><!--把标题的区域划出来--><section data-autoskip=\"1\" style=\"padding: 5px 15px;max-width: 100%;box-sizing: border-box;word-wrap: break-word !important;background-image: url(&quot;http://mmbiz.qpic.cn/mmbiz_png/nyA6UFSJLqxUKq7a7CrR3ic5GWULpltLcuhbAbwAXicYgJKNjG3MZXlLgTpgqE0McTgyL4LpR3pKu1f4qs0zMKZQ/0?wx_fmt=png&quot;);background-attachment: initial;background-size: 100% 100%;background-origin: initial;background-clip: initial;background-position: 0% 0%;background-repeat: no-repeat;\"><!--核心section--><span style=\"max-width: 100%;color: rgb(217, 33, 66);box-sizing: border-box !important;word-wrap: break-word !important;\">"+str(count) + "."+ item.company+"</span></section></section></section></section><!--时间信息--><p style=\"line-height: 25.6px;white-space: normal;max-width: 100%;min-height: 1em;text-align: center;box-sizing: border-box !important;word-wrap: break-word !important;\"><span style=\"max-width: 100%;font-size: 14px;box-sizing: border-box !important;word-wrap: break-word !important;\">时间：<span style=\"max-width: 100%;color: #5D5D5D;\">"+item.strtime+"</span></span></p><!--地点信息--><p style=\"line-height: 25.6px;white-space: normal;max-width: 100%;min-height: 1em;text-align: center;box-sizing: border-box !important;word-wrap: break-word !important;\"><span style=\"max-width: 100%;font-size: 14px;box-sizing: border-box !important;word-wrap: break-word !important;\">地点：<span style=\"max-width: 100%;color: #888888;box-sizing: border-box !important;word-wrap: break-word !important;\"><span style=\"color: #5D5D5D;\">"+item.addr+"</span></span></span></p><p style=\"line-height: 25.6px;white-space: normal;max-width: 100%;min-height: 1em;box-sizing: border-box !important;word-wrap: break-word !important;\"><br/></p>"
        count +=1;
    htmltext += "<section style=\"font-size: 16px;white-space: normal;max-width: 100%;box-sizing: border-box;color: rgb(62, 62, 62);line-height: 23.2727px;background-color: rgb(255, 255, 255);word-wrap: break-word !important;\"><section style=\"max-width: 100%;box-sizing: border-box;word-wrap: break-word !important;\"><section  style=\"margin-top: 10px;margin-bottom: 10px;max-width: 100%;box-sizing: border-box;text-align: center;word-wrap: break-word !important;\"><section  style=\"max-width: 100%;box-sizing: border-box;display: inline-block;vertical-align: top;word-wrap: break-word !important;\"><section  style=\"padding-right: 12px;padding-left: 12px;max-width: 100%;box-sizing: border-box;font-size: 14px;word-wrap: break-word !important;background-color: rgb(254, 255, 255);\"><section style=\"max-width: 100%;box-sizing: border-box;line-height: 23.2727px;word-wrap: break-word !important;background-color: rgb(255, 255, 255);\"><section style=\"max-width: 100%;box-sizing: border-box;word-wrap: break-word !important;\"><section  style=\"margin-top: 10px;margin-bottom: 10px;max-width: 100%;box-sizing: border-box;word-wrap: break-word !important;\"><section  style=\"margin-top: -12px;padding: 10px;max-width: 100%;box-sizing: border-box;border-width: 2px;border-style: solid;border-color: rgb(15, 152, 226);width: 556.364px;word-wrap: break-word !important;\"><section style=\"max-width: 100%;box-sizing: border-box;word-wrap: break-word !important;\"><section  style=\"max-width: 100%;box-sizing: border-box;word-wrap: break-word !important;\"><section  style=\"max-width: 100%;box-sizing: border-box;color: rgb(160, 160, 160);line-height: 3;word-wrap: break-word !important;\"><p style=\"max-width: 100%;box-sizing: border-box;min-height: 1em;word-wrap: break-word !important;\"><span style=\"max-width: 100%;box-sizing: border-box;letter-spacing: 0px;line-height: 3;word-wrap: break-word !important;\">编辑/自行修改</span></p></section></section></section></section></section></section></section><p style=\"max-width: 100%;min-height: 1em;line-height: 23.2727px;box-sizing: border-box !important;word-wrap: break-word !important;\"><img data-ratio=\"0.47368421052631576\" data-s=\"300,640\" src=\"http://mmbiz.qpic.cn/mmbiz_jpg/RW0pj7KFicIOYsFMquDmhHict8ia9CXpVO3o5MZexCX3ZJRe9BoiaT6zYUZ318WBrbFu3icUytgXfpDEv1qLWia2jo6g/640?wx_fmt=jpeg\" data-type=\"jpeg\" data-w=\"950\" width=\"556.359px\" style=\"box-sizing: border-box !important; word-wrap: break-word !important; visibility: visible !important; width: 556.359px !important; height: auto !important;\" _width=\"556.359px\" src=\"http://mmbiz.qpic.cn/mmbiz_jpg/RW0pj7KFicIOYsFMquDmhHict8ia9CXpVO3o5MZexCX3ZJRe9BoiaT6zYUZ318WBrbFu3icUytgXfpDEv1qLWia2jo6g/640?wx_fmt=jpeg&amp;tp=webp&amp;wxfrom=5&amp;wx_lazy=1\" data-fail=\"0\"></p><p style=\"max-width: 100%;min-height: 1em;line-height: 23.2727px;text-align: left;box-sizing: border-box !important;word-wrap: break-word !important;\">点击<strong style=\"max-width: 100%;box-sizing: border-box !important;word-wrap: break-word !important;\"><span style=\"max-width: 100%;color: rgb(255, 104, 39);box-sizing: border-box !important;word-wrap: break-word !important;\">阅读原文</span></strong>了解更多详情</p></section></section></section></section></section>"
    return htmltext


# 用户交互&顶层函数
infostr = ""
inforL = []
urllist = []
days = raw_input(("你想获得几天后的信息？（默认为2，输入w/W获取下周信息)").encode('gbk'))
if ((days != 'w') & (days != 'W') & (~days.isdigit())):
    # daytime = time.strftime('%Y-%m-%d', time.localtime(time.time() + 2 * 86400))
    daytimestr = time.strftime('%Y-%m-%d', time.localtime(time.time() + 2 * 86400))
    # daytime2 = time.strftime('%Y-%m-%d', time.localtime(time.time() + 2 * 86400))
    daytimestr2 = time.strftime('%Y-%m-%d', time.localtime(time.time() + 2 * 86400))
elif ((days == 'w') | (days == 'W')):
    daytimestr = time.strftime('%Y-%m-%d',
                               time.localtime(time.time() + (7 - time.localtime(time.time()).tm_wday) * 86400))
    daytimestr2 = time.strftime('%Y-%m-%d',
                                time.localtime(time.time() + (13 - time.localtime(time.time()).tm_wday) * 86400))
else:
    daytimestr = time.strftime('%Y-%m-%d', time.localtime(time.time() + int(days) * 86400))
    daytimestr2 = time.strftime('%Y-%m-%d', time.localtime(time.time() + int(days) * 86400))
url = "http://job.hust.edu.cn/searchJob.jspx?sdate=" + daytimestr + "&edate=" + daytimestr2 + "&type=11"
try:
    handle = open(daytimestr2 + '.txt', str('w'))
except:
    handle = open(daytimestr2 + '.txt', str('a'))
(inforL, urllist) = getUlist(url, infostr, handle, inforL, urllist)
inforL = getMlist(inforL, time.strptime(daytimestr + " 01:00", "%Y-%m-%d %H:%M"), time.strptime(daytimestr2 + " 23:00", "%Y-%m-%d %H:%M"), 1, urllist)
sortL = sorted(inforL, key=lambda d: d.ttime)
if ((days == 'w') | (days == 'W')):
    handle.write(weekinfo2html(sortL))
else:
    writeFile(sortL, handle)
handle.close()
print "运行完成".encode("gbk")
