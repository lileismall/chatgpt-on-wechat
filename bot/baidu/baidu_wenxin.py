# encoding:utf-8

import requests, json
from bot.bot import Bot
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
from common import dbfunc
import time

BAIDU_API_KEY = conf().get("baidu_wenxin_api_key")
BAIDU_SECRET_KEY = conf().get("baidu_wenxin_secret_key")

WEIXIN_COMMON_STR = "不要用markdown格式回复，消息最终是要发到微信群里,可以多用一些表情"

class BaiduWenxinBot(Bot):

    def __init__(self):
        super().__init__()
        wenxin_model = conf().get("baidu_wenxin_model") or "eb-instant"
        if conf().get("model") and conf().get("model") == "wenxin-4":
            wenxin_model = "completions_pro"
        self.sessions = SessionManager(BaiduWenxinSession, model=wenxin_model)
        
    def get_weather(self):
        # return json
        #{'status': '1', 'count': '1', 'info': 'OK', 'infocode': '10000', 'lives': [{'province': '上海', 'city': '上海市', 
        # 'adcode': '310000', 'weather': '多云', 'temperature': '17', 'winddirection': '北', 'windpower': '≤3', 'humidity': '68', 
        # 'reporttime': '2024-03-31 17:01:22', 'temperature_float': '17.0', 'humidity_float': '68.0'}]}
        # city 编码
        city = "310000" #上海
        key = "85b7745f8f94a00122adb8caa9002df9"
        url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={city}&key={key}"

        response = requests.get(url)

        return response.json()
        
    def my_reply_text(self, query, context):
        nick_name = context.kwargs["msg"].actual_user_nickname
        if query == "打卡":
            dbfunc.insert_info(nick_name)

        week_cnt =  dbfunc.get_cnt_by_name(nick_name, "week")
        month_cnt = dbfunc.get_cnt_by_name(nick_name, "month")
        all_cnt =  dbfunc.get_cnt_by_name(nick_name, "all")
  
        info_str = f'''
本周已累计打卡次数：{week_cnt},
本月已累计打卡次数：{month_cnt},
总累计打卡次数：   {all_cnt}
        '''
  
        if query == "打卡":
            reply_conent = "打卡成功!" + info_str
        elif query == "查询":
            reply_conent = info_str
        else:
            reply_conent = "不支持的操作"
        
        return reply_conent
    
    def get_reply_by_agi(self, new_query, session_id):
        session = self.sessions.session_query(new_query, session_id)
        result = self.reply_text(session)
        total_tokens, completion_tokens, reply_content = (
            result["total_tokens"],
            result["completion_tokens"],
            result["content"],
        )
        logger.debug(
            "[BAIDU] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(session.messages, session_id, reply_content, completion_tokens)
        )

        if total_tokens == 0:
            reply = Reply(ReplyType.ERROR, reply_content)
        else:
            self.sessions.session_reply(reply_content, session_id, total_tokens)
            reply = Reply(ReplyType.TEXT, reply_content)
        return reply

    def reply(self, query, context=None):
        # acquire reply content
        if context and context.type:
            if context.type == ContextType.TEXT:
                logger.info("[BAIDU] query={}".format(query))
                session_id = context["session_id"]
                reply = None
                if query == "#清除记忆":
                    self.sessions.clear_session(session_id)
                    reply = Reply(ReplyType.INFO, "记忆已清除")
                elif query == "#清除所有":
                    self.sessions.clear_all_session()
                    reply = Reply(ReplyType.INFO, "所有人记忆已清除")
                elif query == "周榜":
                    info_str = dbfunc.get_week_top10()
                    logger.debug(f"[BAIDU] top_str={info_str}")
                    reply = self.get_reply_by_agi(f"周榜：{info_str}\n 你是一个记录公司运动打卡的人，根据上面的锻炼打卡数据，重新组织一下语句，数据显示整洁，整体尽量简短, 做一些解析，{WEIXIN_COMMON_STR}", session_id)
                    return reply
                elif query == "月榜":
                    info_str = dbfunc.get_week_top10()
                    logger.debug(f"[BAIDU] top_str={info_str}")
                    reply = self.get_reply_by_agi(f"月榜：{info_str}\n 你是一个记录公司运动打卡的人，根据上面的锻炼打卡数据，重新组织一下语句，数据显示整洁，整体尽量简短, 做一些解析，{WEIXIN_COMMON_STR}", session_id)
                    return reply
                elif query == "总榜":
                    info_str = dbfunc.get_week_top10()
                    logger.debug(f"[BAIDU] top_str={info_str}")
                    reply = self.get_reply_by_agi(f"总榜：{info_str}\n 你是一个记录公司运动打卡的人，根据上面的锻炼打卡数据，重新组织一下语句，数据显示整洁，整体尽量简短, 做一些解析，{WEIXIN_COMMON_STR}", session_id)
                    return reply
                
                elif query == "打卡" or query == "查询":
                    info_str = self.my_reply_text(query, context)
                    # weather_json = self.get_weather()
                    # weather_str = f"上海天气：{wifeather_json['lives'][0]['weather']}, 温度：{weather_json['lives'][0]['temperature']}度"
                    time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                    # current_date_time_str = f"当前时间：{time_str}" if query == "打卡" else ""
                    new_query = f"{info_str} \n你是公司里记录员工打卡的工作人员，根据上面的锻炼打卡数据，重新组织一下语句，数据显示整洁，整体尽量简短,{WEIXIN_COMMON_STR}"
                    reply = self.get_reply_by_agi(new_query, session_id)
                    return reply
                elif query == "查询":
                    info_str = self.my_reply_text(query, context)
                    # weather_json = self.get_weather()
                    # weather_str = f"上海天气：{weather_json['lives'][0]['weather']}, 温度：{weather_json['lives'][0]['temperature']}度"
                    new_query = f"{info_str} \n根据上面的查询到的锻炼打卡数据，重新组织一下语言回复查询的人，数据显示整洁，整体尽量简短,{WEIXIN_COMMON_STR}"
                    reply = self.get_reply_by_agi(new_query, session_id)
                    return reply
                    
                else:
                    session = self.sessions.session_query(query, session_id)
                    result = self.reply_text(session)
                    total_tokens, completion_tokens, reply_content = (
                        result["total_tokens"],
                        result["completion_tokens"],
                        result["content"],
                    )
                    logger.debug(
                        "[BAIDU] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(session.messages, session_id, reply_content, completion_tokens)
                    )

                    if total_tokens == 0:
                        reply = Reply(ReplyType.ERROR, reply_content)
                    else:
                        self.sessions.session_reply(reply_content, session_id, total_tokens)
                        reply = Reply(ReplyType.TEXT, reply_content)
                return reply
            elif context.type == ContextType.IMAGE_CREATE:
                ok, retstring = self.create_img(query, 0)
                reply = None
                if ok:
                    reply = Reply(ReplyType.IMAGE_URL, retstring)
                else:
                    reply = Reply(ReplyType.ERROR, retstring)
                return reply

    def reply_text(self, session: BaiduWenxinSession, retry_count=0):
        try:
            logger.info("[BAIDU] model={}".format(session.model))
            access_token = self.get_access_token()
            if access_token == 'None':
                logger.warn("[BAIDU] access token 获取失败")
                return {
                    "total_tokens": 0,
                    "completion_tokens": 0,
                    "content": 0,
                    }
            url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/" + session.model + "?access_token=" + access_token
            
            headers = {
                'Content-Type': 'application/json'
            }
            payload = {'messages': session.messages}
            response = requests.request("POST", url, headers=headers, data=json.dumps(payload))
            response_text = json.loads(response.text)
            logger.info(f"[BAIDU] response text={response_text}")
            res_content = response_text["result"]
            total_tokens = response_text["usage"]["total_tokens"]
            completion_tokens = response_text["usage"]["completion_tokens"]
            logger.info("[BAIDU] reply={}".format(res_content))
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": res_content,
            }
        except Exception as e:
            need_retry = retry_count < 2
            logger.warn("[BAIDU] Exception: {}".format(e))
            need_retry = False
            self.sessions.clear_session(session.session_id)
            result = {"completion_tokens": 0, "content": "出错了: {}".format(e)}
            return result

    def get_access_token(self):
        """
        使用 AK，SK 生成鉴权签名（Access Token）
        :return: access_token，或是None(如果错误)
        """
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {"grant_type": "client_credentials", "client_id": BAIDU_API_KEY, "client_secret": BAIDU_SECRET_KEY}
        return str(requests.post(url, params=params).json().get("access_token"))
