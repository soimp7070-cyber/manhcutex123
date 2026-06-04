#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests, re, os, json, base64, uuid, random, sys, time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pystyle import Colors, Colorate

# ------------------------- GRADIENT & UI -------------------------
def gradient_3(text):
    def rgb_to_ansi(r, g, b):
        return f"\033[38;2;{r};{g};{b}m"
    colors = [(255,255,255),(255,255,220),(255,245,180),(255,235,120),(255,215,80),(255,190,60),
              (255,160,40),(255,130,30),(255,100,25),(255,70,20),(220,50,15)]
    result, length = "", len(text)
    for i, char in enumerate(text):
        t = i / (length - 1 if length > 1 else 1)
        segment = t * (len(colors) - 1)
        idx1 = int(segment)
        idx2 = min(idx1 + 1, len(colors) - 1)
        ratio = segment - idx1
        r = int(colors[idx1][0] + (colors[idx2][0] - colors[idx1][0]) * ratio)
        g = int(colors[idx1][1] + (colors[idx2][1] - colors[idx1][1]) * ratio)
        b = int(colors[idx1][2] + (colors[idx2][2] - colors[idx1][2]) * ratio)
        result += rgb_to_ansi(r,g,b) + char
    return result + "\033[0m"

def gradient_tutu(text):
    def rgb_to_ansi(r,g,b): return f"\033[38;2;{r};{g};{b}m"
    start, mid, end = (0,255,255),(255,0,255),(255,255,0)
    steps = len(text)
    result = ""
    for i, char in enumerate(text):
        t = i / (steps - 1 if steps > 1 else 1)
        if t < 0.5:
            t2 = t / 0.5
            r = int(start[0] + (mid[0]-start[0])*t2)
            g = int(start[1] + (mid[1]-start[1])*t2)
            b = int(start[2] + (mid[2]-start[2])*t2)
        else:
            t2 = (t-0.5)/0.5
            r = int(mid[0] + (end[0]-mid[0])*t2)
            g = int(mid[1] + (end[1]-mid[1])*t2)
            b = int(mid[2] + (end[2]-mid[2])*t2)
        result += rgb_to_ansi(r,g,b) + char
    return result + "\033[0m"

def print_rtv(text, end='\n'):
    print(gradient_tutu(text) + "\033[0m", end=end, flush=True)

def input_rtv(prompt):
    return input(gradient_tutu(prompt) + "\033[0m")

def thanhngang(so):
    print(gradient_tutu('─' * so))

def print_job_success(stt, timejob, type_, id_, msg, xu):
    stt_text = f"\033[1;37m{stt}"
    time_text = gradient_3(timejob)
    type_text = f"\033[1;37m{type_.upper()}"
    id_text = gradient_3(id_)
    msg_text = f"\033[1;37m{msg}"
    xu_text = f"\033[1;37m{str(format(int(xu.replace(',', '')), ','))}"
    result = (f"\033[1;37m[ {stt_text}\033[1;37m ]\033[1;37m[ {type_text}\033[1;37m ]"
              f"\033[1;37m[ {time_text}\033[1;37m ]\033[1;37m[ {msg_text}\033[1;37m ]"
              f"\033[1;37m[ {id_text}\033[1;37m ]\033[1;37m[ {xu_text}\033[1;37m ]")
    print(result, flush=True)

def banner():
    banner_text = r"""
██╗  ██╗███╗   ███╗██╗  ██╗
██║  ██║████╗ ████║██║ ██╔╝
███████║██╔████╔██║█████╔╝ 
██╔══██║██║╚██╔╝██║██╔═██╗ 
██║  ██║██║ ╚═╝ ██║██║  ██╗
╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝
"""
    rainbow_banner = Colorate.Diagonal(Colors.rainbow, banner_text, 1)
    print(rainbow_banner)
    thanhngang(65)
    print_rtv("[</>] BOX ZALO : https://zalo.me/g/rcryht808")    
    print_rtv("[</>] WEBSITE : https://tainguyensieure.store")
    thanhngang(65)

def Delay(value):
    if isinstance(value, tuple) and len(value) == 2:
        min_delay, max_delay = value
        delay_time = random.uniform(float(min_delay), float(max_delay))
    else:
        delay_time = float(value)
    if delay_time <= 0:
        return
    total_blocks = 15
    start_time = time.time()
    end_time = start_time + delay_time
    animation_speed = 2
    last_frame_time = start_time
    while time.time() < end_time:
        current_time = time.time()
        remaining = end_time - current_time
        if current_time - last_frame_time >= 0.02:
            elapsed = current_time - start_time
            block_pos = int(elapsed * animation_speed * 4) % total_blocks
            progress_bar = ''.join('■' if i == block_pos else '▪' for i in range(total_blocks))
            colored_bar = gradient_tutu(progress_bar)
            remaining_str = f"{remaining:.1f}"
            if len(remaining_str) == 3:
                remaining_str = " " + remaining_str
            display_text = (f"\033[1;37m[ {gradient_3('vphuc.luv')}\033[1;37m ][ {gradient_3('Chờ Đợi Là Hạnh Phúc')}\033[1;37m ]"
                            f"[ \033[1;37m{remaining_str}\033[1;37m ]")
            full_display = f"{display_text}[ {colored_bar}\033[1;37m ]"
            print(full_display, end='\r', flush=True)
            last_frame_time = current_time
        time.sleep(0.005)
    print(' ' * 70, end='\r', flush=True)

def encode_to_base64(_data):
    return base64.b64encode(_data.encode('utf-8')).decode('utf-8')

# ------------------------- CLASS FACEBOOK -------------------------
class Facebook:
    def __init__(self, cookie, proxy=None):
        self.lsd = ''
        self.actor_id = ''
        self.fb_dtsg = ''
        self.jazoest = ''
        self.session = requests.Session()
        self.proxies = None

        matches = re.findall('i_user=.*?;', cookie)
        if matches:
            cookie = cookie.replace(matches[0], '')
        self.cookie = cookie
        self.headers = {
            'authority': 'www.facebook.com',
            'accept': '*/*',
            'cookie': self.cookie,
            'origin': 'https://www.facebook.com',
            'referer': 'https://www.facebook.com/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin'
        }

        if proxy:
            try:
                parts = proxy.strip().split(':')
                if len(parts) == 4:
                    host, port, user, pwd = parts
                    self.proxies = {
                        'http': f'http://{user}:{pwd}@{host}:{port}',
                        'https': f'http://{user}:{pwd}@{host}:{port}'
                    }
                elif len(parts) == 2:
                    host, port = parts
                    self.proxies = {
                        'http': f'http://{host}:{port}',
                        'https': f'http://{host}:{port}'
                    }
            except:
                self.proxies = None
            if self.proxies:
                self.session.proxies.update(self.proxies)

        try:
            resp = self.session.get('https://www.facebook.com/', headers=self.headers, timeout=30).text
            dtsg = re.findall(r'\["DTSGInitialData",\[\],\{"token":"(.*?)"\}', resp)
            if dtsg:
                self.fb_dtsg = dtsg[0]
                self.jazoest = re.findall(r'jazoest=(.*?)\"', resp)[0]
                self.actor_id = re.findall(r'\"ACCOUNT_ID\":\"(.*?)\"', resp)[0]
                self.lsd = re.findall(r'\["LSD",\[\],\{"token":"(.*?)\"\}', resp)[0]
        except:
            pass

    def get_profile(self):
        try:
            data = {
                'av': self.actor_id, '__user': self.actor_id, '__a': '1',
                'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest, 'lsd': self.lsd,
                'variables': '{"showUpdatedLaunchpointRedesign":true,"useAdminedPagesForActingAccount":false,"useNewPagesYouManage":true}',
                'doc_id': '5300338636681652'
            }
            resp = self.session.post('https://www.facebook.com/api/graphql/', headers=self.headers, data=data, proxies=self.proxies).json()
            nodes = resp['data']['viewer']['actor']['profile_switcher_eligible_profiles']['nodes']
            return len(nodes), nodes
        except:
            return 0, []

    def info(self, actor_id):
        headers = self.headers.copy()
        headers['cookie'] = headers['cookie'] + f';i_user={actor_id}'
        try:
            get = self.session.get('https://www.facebook.com/me', headers=headers, proxies=self.proxies).text
            name = get.split('<title>')[1].split('</title>')[0]
            return {'success': 200, 'id': actor_id, 'name': name}
        except:
            return {'error': 200}

    def reaction(self, id, actor_id, typ):
        try:
            headers = self.headers.copy()
            headers['cookie'] = headers['cookie'] + f';i_user={actor_id}'
            reac_map = {"LIKE":"1635855486666999","LOVE":"1678524932434102","CARE":"613557422527858",
                        "HAHA":"115940658764963","WOW":"478547315650144","SAD":"908563459236466","ANGRY":"444813342392137"}
            idreac = reac_map.get(typ)
            variables = {
                "input": {
                    "attribution_id_v2": "CometHomeRoot.react,comet.home,tap_tabbar,1719027162723,322693,4748854339,,",
                    "feedback_id": encode_to_base64(f"feedback:{id}"),
                    "feedback_reaction_id": idreac,
                    "feedback_source": "NEWS_FEED",
                    "is_tracking_encrypted": True,
                    "tracking": [],
                    "session_id": str(uuid.uuid4()),
                    "actor_id": actor_id,
                    "client_mutation_id": "3"
                },
                "useDefaultActor": False,
                "__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider": False
            }
            data = {
                'av': actor_id, '__user': actor_id, '__a': '1',
                'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest, 'lsd': self.lsd,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CometUFIFeedbackReactMutation',
                'variables': json.dumps(variables),
                'server_timestamps': 'true',
                'doc_id': '7047198228715224',
            }
            self.session.post("https://www.facebook.com/api/graphql/", headers=headers, data=data, proxies=self.proxies)
        except:
            pass

    def follow(self, id, actor_id):
        try:
            headers = self.headers.copy()
            headers['cookie'] = headers['cookie'] + f';i_user={actor_id}'
            variables = {
                "input": {
                    "subscribe_location": "PROFILE",
                    "subscribee_id": id,
                    "actor_id": actor_id,
                    "client_mutation_id": "1"
                },
                "scale": 1
            }
            data = {
                'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest, 'lsd': self.lsd,
                'variables': json.dumps(variables),
                'doc_id': '5032256523527306'
            }
            self.session.post('https://www.facebook.com/api/graphql/', headers=headers, data=data, proxies=self.proxies)
        except:
            pass

    def like_page(self, id, actor_id):
        try:
            headers = self.headers.copy()
            headers['cookie'] = headers['cookie'] + f';i_user={actor_id}'
            variables = {
                "input": {
                    "is_tracking_encrypted": True,
                    "page_id": id,
                    "source": "unknown",
                    "tracking": [],
                    "actor_id": actor_id,
                    "client_mutation_id": "2"
                },
                "isAdminView": False
            }
            data = {
                'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest, 'lsd': self.lsd,
                'variables': json.dumps(variables),
                'doc_id': '5556947024325929'
            }
            self.session.post('https://www.facebook.com/api/graphql/', headers=headers, data=data, proxies=self.proxies)
        except:
            pass

    def reactioncmt(self, id, actor_id, typ):
        try:
            headers = self.headers.copy()
            headers['cookie'] = headers['cookie'] + f';i_user={actor_id}'
            reac_map = {"LIKE":"1635855486666999","LOVE":"1678524932434102","CARE":"613557422527858",
                        "HAHA":"115940658764963","WOW":"478547315650144","SAD":"908563459236466","ANGRY":"444813342392137"}
            idreac = reac_map.get(typ)
            timestamp = str(int(datetime.now().timestamp() * 1000))
            variables = {
                "input": {
                    "attribution_id_v2": "CometVideoHomeNewPermalinkRoot.react,comet.watch.injection,via_cold_start,1719930662698,975645,2392950137,,",
                    "feedback_id": encode_to_base64(f"feedback:{id}"),
                    "feedback_reaction_id": idreac,
                    "feedback_source": "TAHOE",
                    "is_tracking_encrypted": True,
                    "tracking": [],
                    "session_id": str(uuid.uuid4()),
                    "downstream_share_session_id": str(uuid.uuid4()),
                    "downstream_share_session_origin_uri": "https://fb.watch/t3OatrTuqv/?mibextid=Nif5oz",
                    "downstream_share_session_start_time": timestamp,
                    "actor_id": actor_id,
                    "client_mutation_id": "1"
                },
                "useDefaultActor": False,
                "__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider": False
            }
            data = {
                'av': actor_id, 'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest, 'lsd': self.lsd,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'CometUFIFeedbackReactMutation',
                'variables': json.dumps(variables),
                'server_timestamps': 'true',
                'doc_id': '7616998081714004',
            }
            self.session.post('https://www.facebook.com/api/graphql/', headers=headers, data=data, proxies=self.proxies)
        except:
            pass

    def group(self, id, actor_id):
        try:
            headers = self.headers.copy()
            headers['cookie'] = headers['cookie'] + f';i_user={actor_id}'
            variables = {
                "feedType": "DISCUSSION",
                "groupID": id,
                "imageMediaType": "image/x-auto",
                "input": {
                    "action_source": "GROUP_MALL",
                    "attribution_id_v2": "CometGroupDiscussionRoot.react,comet.group,via_cold_start,1673041528761,114928,2361831622,",
                    "group_id": id,
                    "group_share_tracking_params": {
                        "app_id": "2220391788200892",
                        "exp_id": "null",
                        "is_from_share": False
                    },
                    "actor_id": actor_id,
                    "client_mutation_id": "1"
                },
                "inviteShortLinkKey": None,
                "isChainingRecommendationUnit": False,
                "isEntityMenu": True,
                "scale": 2,
                "source": "GROUP_MALL",
                "renderLocation": "group_mall",
                "__relay_internal__pv__GroupsCometEntityMenuEmbeddedrelayprovider": True,
                "__relay_internal__pv__GlobalPanelEnabledrelayprovider": False
            }
            data = {
                'av': actor_id, '__user': actor_id, '__a': '1',
                'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest, 'lsd': self.lsd,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'GroupCometJoinForumMutation',
                'variables': json.dumps(variables),
                'server_timestamps': 'true',
                'doc_id': '5853134681430324',
            }
            self.session.post('https://www.facebook.com/api/graphql/', headers=headers, data=data, proxies=self.proxies)
        except:
            pass

    def share(self, id, actor_id):
        try:
            headers = self.headers.copy()
            headers['cookie'] = headers['cookie'] + f';i_user={actor_id}'
            variables = {
                "input": {
                    "composer_entry_point": "share_modal",
                    "composer_source_surface": "feed_story",
                    "composer_type": "share",
                    "idempotence_token": f"{uuid.uuid4()}_FEED",
                    "source": "WWW",
                    "attachments": [{
                        "link": {
                            "share_scrape_data": json.dumps({"share_type": 22, "share_params": [id]})
                        }
                    }],
                    "reshare_original_post": "RESHARE_ORIGINAL_POST",
                    "audience": {"privacy": {"allow": [], "base_state": "EVERYONE", "deny": [], "tag_expansion_state": "UNSPECIFIED"}},
                    "is_tracking_encrypted": True,
                    "tracking": [],
                    "logging": {"composer_session_id": str(uuid.uuid4())},
                    "navigation_data": {
                        "attribution_id_v2": "FeedsCometRoot.react,comet.most_recent_feed,tap_bookmark,1719641912186,189404,608920319153834,,"
                    },
                    "event_share_metadata": {"surface": "newsfeed"},
                    "actor_id": actor_id,
                    "client_mutation_id": "3"
                },
                "feedLocation": "NEWSFEED",
                "feedbackSource": 1,
                "focusCommentID": None,
                "gridMediaWidth": None,
                "groupID": None,
                "scale": 1,
                "privacySelectorRenderLocation": "COMET_STREAM",
                "checkPhotosToReelsUpsellEligibility": False,
                "renderLocation": "homepage_stream",
                "useDefaultActor": False,
                "inviteShortLinkKey": None,
                "isFeed": True,
                "isFundraiser": False,
                "isFunFactPost": False,
                "isGroup": False,
                "isEvent": False,
                "isTimeline": False,
                "isSocialLearning": False,
                "isPageNewsFeed": False,
                "isProfileReviews": False,
                "isWorkSharedDraft": False,
                "hashtag": None,
                "canUserManageOffers": False,
                "__relay_internal__pv__CometUFIShareActionMigrationrelayprovider": True,
                "__relay_internal__pv__IncludeCommentWithAttachmentrelayprovider": True,
                "__relay_internal__pv__CometUFIReactionsEnableShortNamerelayprovider": False,
                "__relay_internal__pv__CometImmersivePhotoCanUserDisable3DMotionrelayprovider": False,
                "__relay_internal__pv__IsWorkUserrelayprovider": False,
                "__relay_internal__pv__IsMergQAPollsrelayprovider": False,
                "__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider": True,
                "__relay_internal__pv__StoriesRingrelayprovider": False,
                "__relay_internal__pv__EventCometCardImage_prefetchEventImagerelayprovider": False
            }
            data = {
                'av': actor_id, '__user': actor_id, '__a': '1',
                'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest, 'lsd': self.lsd,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'ComposerStoryCreateMutation',
                'variables': json.dumps(variables),
                'server_timestamps': 'true',
                'doc_id': '8167261726632010'
            }
            self.session.post("https://www.facebook.com/api/graphql/", headers=headers, data=data, proxies=self.proxies)
        except:
            pass

    def comment(self, id, actor_id, msg):
        try:
            headers = self.headers.copy()
            headers['cookie'] = headers['cookie'] + f';i_user={actor_id}'
            variables = {
                "feedLocation": "DEDICATED_COMMENTING_SURFACE",
                "feedbackSource": 110,
                "groupID": None,
                "input": {
                    "client_mutation_id": "4",
                    "actor_id": actor_id,
                    "attachments": None,
                    "feedback_id": encode_to_base64(f"feedback:{id}"),
                    "formatting_style": None,
                    "message": {"ranges": [], "text": msg},
                    "attribution_id_v2": "CometHomeRoot.react,comet.home,via_cold_start,1718688700413,194880,4748854339,,",
                    "vod_video_timestamp": None,
                    "feedback_referrer": "/",
                    "is_tracking_encrypted": True,
                    "tracking": [],
                    "feedback_source": "DEDICATED_COMMENTING_SURFACE",
                    "idempotence_token": f"client:{uuid.uuid4()}",
                    "session_id": str(uuid.uuid4())
                },
                "inviteShortLinkKey": None,
                "renderLocation": None,
                "scale": 1,
                "useDefaultActor": False,
                "focusCommentID": None
            }
            data = {
                'av': actor_id, 'fb_dtsg': self.fb_dtsg, 'jazoest': self.jazoest, 'lsd': self.lsd,
                'fb_api_caller_class': 'RelayModern',
                'fb_api_req_friendly_name': 'useCometUFICreateCommentMutation',
                'variables': json.dumps(variables),
                'server_timestamps': 'true',
                'doc_id': '7994085080671282',
            }
            self.session.post('https://www.facebook.com/api/graphql/', headers=headers, data=data, proxies=self.proxies)
        except:
            pass

# ------------------------- CLASS TUONGTACCHEO (KHÔNG CAPTCHA) -------------------------
class TuongTacCheo:
    def __init__(self, token, proxy=None):
        self.ss = requests.Session()
        self.proxies = None
        if proxy:
            try:
                parts = proxy.strip().split(':')
                if len(parts) == 4:
                    host, port, user, pwd = parts
                    self.proxies = {
                        'http': f'http://{user}:{pwd}@{host}:{port}',
                        'https': f'http://{user}:{pwd}@{host}:{port}'
                    }
                elif len(parts) == 2:
                    host, port = parts
                    self.proxies = {
                        'http': f'http://{host}:{port}',
                        'https': f'http://{host}:{port}'
                    }
            except:
                self.proxies = None
            if self.proxies:
                self.ss.proxies.update(self.proxies)

        session = self.ss.post('https://tuongtaccheo.com/logintoken.php', data={'access_token': token}, timeout=30)
        self.cookie = session.headers.get('Set-cookie', '')
        self.session = session.json()
        self.headers = {
            'Host': 'tuongtaccheo.com',
            'accept': '*/*',
            'origin': 'https://tuongtaccheo.com',
            'x-requested-with': 'XMLHttpRequest',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'cookie': self.cookie
        }

    def info(self):
        if self.session.get('status') == 'success':
            return {'status': "success", 'user': self.session['data']['user'], 'xu': self.session['data']['sodu']}
        return {'error': 200}

    def cauhinh(self, id):
        try:
            resp = self.ss.post('https://tuongtaccheo.com/cauhinh/datnick.php', headers=self.headers, data={'iddat[]': id, 'loai': 'fb'}, timeout=30).text
            return resp == '1'
        except:
            return False

    def getjob(self, nv):
        try:
            return self.ss.get(f'https://tuongtaccheo.com/kiemtien/{nv}/getpost.php', headers=self.headers, timeout=30)
        except:
            return None

    def nhanxu(self, id, nv):
        try:
            home = self.ss.get('https://tuongtaccheo.com/home.php', headers=self.headers, timeout=30).text
            xu_truoc = int(home.split('"soduchinh">')[1].split('<')[0].replace(',',''))
            resp = self.ss.post(f'https://tuongtaccheo.com/kiemtien/{nv}/nhantien.php', headers=self.headers, data={'id': id}, timeout=30).json()
            home2 = self.ss.get('https://tuongtaccheo.com/home.php', headers=self.headers, timeout=30).text
            xu_sau = int(home2.split('"soduchinh">')[1].split('<')[0].replace(',',''))
            if 'mess' in resp and xu_sau > xu_truoc:
                msg = resp['mess'].split()[-2]
                return {'status': "success", 'msg': f'+{msg} Xu', 'xu': str(xu_sau)}
            return {'error': 200}
        except:
            return {'error': 200}

# ------------------------- HÀM PHỤ TRỢ -------------------------
def check_proxy(proxy):
    try:
        parts = proxy.strip().split(':')
        if len(parts) == 4:
            host, port, user, pwd = parts
            proxies = {'http': f'http://{user}:{pwd}@{host}:{port}', 'https': f'http://{user}:{pwd}@{host}:{port}'}
        elif len(parts) == 2:
            host, port = parts
            proxies = {'http': f'http://{host}:{port}', 'https': f'http://{host}:{port}'}
        else:
            return {'status': "error", 'ip': None}
        resp = requests.get('https://api.ipify.org', proxies=proxies, timeout=10)
        if resp.status_code == 200:
            return {'status': "success", 'ip': resp.text}
        return {'status': "error", 'ip': None}
    except:
        return {'status': "error", 'ip': None}

def add_proxy():
    proxy_list = []
    print_rtv("[?] Nhập Proxy Theo Dạng : IP:Port:User:Pass Hoặc IP:Port")
    print_rtv("[!] Nhấn Enter Để Bỏ Qua")
    i = 1
    while True:
        proxy = input_rtv(f'[?] Nhập Proxy Số {i} : ').strip()
        if proxy == '':
            break
        check = check_proxy(proxy)
        if check['status'] == "success":
            i += 1
            print_rtv(f"[✓] Proxy Hoạt Động : {check['ip']}")
            proxy_list.append(proxy)
        else:
            print_rtv("[!] Proxy Die, Vui Lòng Nhập Lại !")
    return proxy_list

def addcookie(proxy):
    listCookie = []
    cookie = input_rtv('[?] Nhập Cookie Facebook Chứa Page : ')
    thanhngang(65)
    fb = Facebook(cookie, proxy)
    total, profiles = fb.get_profile()
    print_rtv(f'[✓] Đã Tìm Thấy {total} Page Profile')
    if total == 0:
        print_rtv("[!] Không tìm thấy page nào trong cookie này")
        return []
    for idx, profile in enumerate(profiles, 1):
        pid = profile['profile']['id']
        pname = profile['profile']['name']
        print_rtv(f'[?] Page {idx} : {pname} | UID : {pid}')
    print_rtv("[?] Nhập 'all' Để Chạy Tất Cả Page")
    print_rtv("[!] Có Thể Chọn Nhiều Page [ Ví Dụ : 1+2+3 ]")
    while True:
        chon = input_rtv('[?] Nhập : ').strip()
        if chon.lower() == 'all':
            for p in profiles:
                pid = p['profile']['id']
                cookie_page = cookie + f';i_user={pid}'
                listCookie.append(cookie_page)
            return listCookie
        if '+' in chon:
            indices = [int(x.strip())-1 for x in chon.split('+') if x.strip().isdigit()]
            for idx in indices:
                if 0 <= idx < total:
                    cookie_page = cookie + f';i_user={profiles[idx]["profile"]["id"]}'
                    listCookie.append(cookie_page)
            return listCookie
        if chon.isdigit():
            idx = int(chon)-1
            if 0 <= idx < total:
                cookie_page = cookie + f';i_user={profiles[idx]["profile"]["id"]}'
                listCookie.append(cookie_page)
            return listCookie
        print_rtv("[!] Nhập sai, vui lòng nhập lại")

def process_cookie(ttc, cookie, proxy, settings, list_nv, totalxu_lock, stt_lock):
    uid_page = cookie.split('i_user=')[1].split(';')[0]
    fb = Facebook(cookie, proxy)
    info = fb.info(uid_page)
    if 'success' not in info:
        print_rtv(f"[!] Cookie Page {uid_page} Die")
        return None

    namefb = info['name']
    idfb = info['id']
    runidfb = settings.get("runidfb", "n")
    idrun = idfb[:3] + "#"*(len(idfb)-3) if runidfb.upper() == 'Y' else idfb

    # Kiểm tra xem UID đã được cấu hình trên TTC chưa
    if not ttc.cauhinh(idfb):
        print_rtv(f"[!] UID Page {idfb} chưa được cấu hình trên TTC. Bỏ qua cookie này.")
        return None

    myip = None
    if proxy:
        ip_check = check_proxy(proxy)
        if ip_check['status'] == "success":
            myip = ip_check['ip']
    print_rtv(f"[✓] UID Page : {idrun} | Page : {namefb} | Proxy : {myip}")

    job_success_count = 0
    job_fail_count = 0
    list_nv_current = list_nv.copy()

    while list_nv_current:
        random_nv = random.choice(list_nv_current)
        fields_map = {
            '1':'likepostvipcheo','2':'likepostvipre','3':'camxucvipcheo',
            '4':'camxucvipre','5':'camxuccheobinhluan','6':'cmtcheo',
            '7':'sharecheo','8':'likepagecheo','9':'subcheo','0':'thamgianhomcheo'
        }
        fields = fields_map.get(random_nv)
        if not fields:
            list_nv_current.remove(random_nv)
            continue

        getjob = ttc.getjob(fields)
        if getjob is None or getjob.status_code != 200:
            time.sleep(2)
            continue

        try:
            data = getjob.json()
        except:
            time.sleep(2)
            continue

        if isinstance(data, list) and data:
            for job in data:
                next_delay = False
                job_id = job['idpost']
                try:
                    if random_nv in ['1','2']:
                        target = job['idfb'].split('_')[1] if '_' in job['idfb'] else job['idfb']
                        fb.reaction(target, idfb, "LIKE")
                        id_show = target
                        typ = 'LIKE'
                    elif random_nv in ['3','4']:
                        target = job['idfb'].split('_')[1] if '_' in job['idfb'] else job['idfb']
                        fb.reaction(target, idfb, job['loaicx'])
                        id_show = target
                        typ = job['loaicx']
                    elif random_nv == '5':
                        fb.reactioncmt(job_id, idfb, job['loaicx'])
                        id_show = job_id
                        typ = job['loaicx']
                    elif random_nv == '6':
                        fb.comment(job_id, idfb, json.loads(job["nd"])[0])
                        id_show = job_id
                        typ = 'COMMENT'
                    elif random_nv == '7':
                        fb.share(job_id, idfb)
                        id_show = job_id
                        typ = 'SHARE'
                    elif random_nv == '8':
                        target = job['UID']
                        fb.like_page(target, idfb)
                        id_show = target
                        typ = 'LIKEPAGE'
                    elif random_nv == '9':
                        target = job.get('UID', job.get('idpost'))
                        fb.follow(target, idfb)
                        id_show = target
                        typ = 'FOLLOW'
                    elif random_nv == '0':
                        target = job.get('UID', job.get('idpost'))
                        fb.group(target, idfb)
                        id_show = target
                        typ = 'GROUP'
                except Exception as e:
                    job_fail_count += 1
                    if job_fail_count >= 20:
                        print_rtv(f"[!] Tài Khoản {namefb} Đã Bị Block / Lỗi Nhiều")
                        return None
                    continue

                nhan = ttc.nhanxu(job_id, fields)
                if nhan.get('status') == 'success':
                    next_delay = True
                    msg = nhan['msg']
                    xu_str = nhan['xu']
                    job_success_count += 1
                    job_fail_count = 0
                    timejob = datetime.now().strftime('%H:%M:%S')
                    with totalxu_lock:
                        totalxu_lock['value'] += int(msg.replace('+','').split()[0])
                    with stt_lock:
                        stt_lock['value'] += 1
                    print_job_success(stt_lock['value'], timejob, typ, id_show, msg, xu_str)
                    if stt_lock['value'] % 10 == 0:
                        print_rtv(f'[ Tổng Cookies : {total_cookies_global} ][ Xu Đã Nhận : {format(totalxu_lock["value"], ",")} ]')
                else:
                    job_fail_count += 1
                    if job_fail_count >= 20:
                        print_rtv(f"[!] Tài Khoản {namefb} Bị Lỗi Nhiều")
                        return None

                if job_success_count >= settings.get("JobBreak", 10):
                    break

                if next_delay:
                    if job_success_count % settings.get("JobbBlock", 5) == 0:
                        Delay(settings.get("DelayBlock", 60))
                    else:
                        Delay(settings.get("delay", (2,5)))

            if job_success_count >= settings.get("JobBreak", 10):
                break
        else:
            if data and 'countdown' in data:
                cd = data['countdown']
                if cd:
                    print_rtv(f'[...] Get Job {fields.upper()}, Delay : {cd:.1f}s', end='\r')
                    Delay(cd)
            else:
                time.sleep(1)
    return {'success': True, 'name': namefb}

# ------------------------- MAIN -------------------------
os.system("cls" if os.name == "nt" else "clear")
banner()

TTC_DATA_DIR = "ttc_data"
if not os.path.exists(TTC_DATA_DIR):
    os.makedirs(TTC_DATA_DIR)

# Đọc danh sách các tài khoản TTC đã lưu
ttc_accounts = {}
for item in os.listdir(TTC_DATA_DIR):
    path = os.path.join(TTC_DATA_DIR, item)
    if os.path.isdir(path) and os.path.exists(os.path.join(path, "info.json")):
        with open(os.path.join(path, "info.json"), "r") as f:
            info = json.load(f)
        ttc_accounts[info['username']] = path

selected_ttc_user = None
if ttc_accounts:
    print_rtv("[✓] Các tài khoản TTC đã lưu:")
    usernames = list(ttc_accounts.keys())
    for i, user in enumerate(usernames, 1):
        print_rtv(f"  {i}. {user}")
    thanhngang(65)
    print_rtv("[?] Nhập số để chọn tài khoản, hoặc '0' để thêm mới")
    while True:
        choice = input_rtv("[?] Chọn : ")
        if choice == '0':
            selected_ttc_user = None
            break
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(usernames):
                selected_ttc_user = usernames[idx]
                break
        except:
            pass
        print_rtv("[!] Lựa chọn không hợp lệ")

if selected_ttc_user is None:
    while True:
        token = input_rtv('[?] Nhập Access_Token TuongTacCheo.Com : ')
        proxy_test = None
        ttc_test = TuongTacCheo(token, proxy_test)
        checktoken = ttc_test.info()
        if checktoken.get('status') == 'success':
            users = checktoken['user']
            xu_ban_dau = checktoken['xu']
            print_rtv("[✓] Đăng Nhập Thành Công")
            ttc_dir = os.path.join(TTC_DATA_DIR, users)
            os.makedirs(ttc_dir, exist_ok=True)
            with open(os.path.join(ttc_dir, "info.json"), "w") as f:
                json.dump({"username": users, "token": token, "xu": xu_ban_dau}, f)
            selected_ttc_user = users
            break
        else:
            print_rtv("[!] Đăng Nhập Thất Bại, thử lại")

# Đường dẫn dữ liệu của TTC user đã chọn
ttc_dir = os.path.join(TTC_DATA_DIR, selected_ttc_user)
with open(os.path.join(ttc_dir, "info.json"), "r") as f:
    ttc_info = json.load(f)
token = ttc_info['token']

# Proxy
proxy_file = os.path.join(ttc_dir, "proxy.json")
if os.path.exists(proxy_file):
    print_rtv("[?] Nhập [ 1 ] Sử Dụng Proxy Đã Lưu")
    print_rtv("[?] Nhập [ 2 ] Nhập Proxy Mới")
    thanhngang(65)
    chon = input_rtv('[?] Nhập Số : ')
    thanhngang(65)
    if chon == '1':
        with open(proxy_file, 'r') as f:
            proxy_list = json.load(f)
    else:
        proxy_list = add_proxy()
        with open(proxy_file, 'w') as f:
            json.dump(proxy_list, f)
else:
    proxy_list = add_proxy()
    with open(proxy_file, 'w') as f:
        json.dump(proxy_list, f)

# Cookie Facebook riêng cho TTC user này
cookie_file = os.path.join(ttc_dir, "cookies.json")
if os.path.exists(cookie_file):
    print_rtv("[?] Nhập [ 1 ] Sử Dụng Cookie Page Đã Lưu")
    print_rtv("[?] Nhập [ 2 ] Nhập Cookie Facebook Page Mới")
    thanhngang(65)
    chon = input_rtv('[?] Nhập Số : ')
    thanhngang(65)
    if chon == '1':
        listCookie = json.load(open(cookie_file, 'r'))
    else:
        proxy_first = proxy_list[0] if proxy_list else None
        listCookie = addcookie(proxy_first)
        with open(cookie_file, 'w') as f:
            json.dump(listCookie, f)
else:
    proxy_first = proxy_list[0] if proxy_list else None
    listCookie = addcookie(proxy_first)
    with open(cookie_file, 'w') as f:
        json.dump(listCookie, f)

if not listCookie:
    print_rtv("[!] Không có cookie nào hợp lệ. Thoát.")
    sys.exit()

os.system("cls" if os.name == "nt" else "clear")
banner()

print_rtv(f"– Tên Tài Khoản TTC : {selected_ttc_user}")
print_rtv(f"– Tổng Cookie : {len(listCookie)}")
thanhngang(65)
print_rtv("- Nhập [ 1 ] Jobs Like Vip")
print_rtv("- Nhập [ 2 ] Jobs Like Thường")
print_rtv("- Nhập [ 3 ] Jobs Cảm Xúc Vip")
print_rtv("- Nhập [ 4 ] Jobs Cảm Xúc Thường")
print_rtv("- Nhập [ 5 ] Jobs Cảm Xúc Comment")
print_rtv("- Nhập [ 6 ] Jobs Comment")
print_rtv("- Nhập [ 7 ] Jobs Share")
print_rtv("- Nhập [ 8 ] Jobs Like Page")
print_rtv("- Nhập [ 9 ] Jobs Follow")
print_rtv("- Nhập [ 0 ] Jobs Group")
print_rtv("- Có Thể Chọn Nhiều Nhiệm Vụ [ VD : 123... ]")
thanhngang(65)

setting_file = os.path.join(ttc_dir, "setting.json")
if os.path.exists(setting_file):
    with open(setting_file, "r", encoding="utf-8") as f:
        settings = json.load(f)
    if isinstance(settings.get("delay"), (int, float)):
        settings["delay"] = (settings["delay"], settings["delay"])
    elif isinstance(settings.get("delay"), list):
        settings["delay"] = tuple(settings["delay"])
    use_saved = input_rtv("[?] Bạn Có Muốn Sử Dụng Cấu Hình Cũ Không [ y / n ] : ")
    if use_saved.lower() == "y":
        print_rtv("[✓] Sử Dụng Cấu Hình Đã Lưu")
        if "nhiemvu" in settings and settings["nhiemvu"]:
            list_nv = list(settings["nhiemvu"])
        else:
            settings["nhiemvu"] = input_rtv("[?] Nhập Số Để Chọn Nhiệm Vụ : ")
            list_nv = list(settings["nhiemvu"])
    else:
        settings = {}
        settings["nhiemvu"] = input_rtv("[?] Nhập Số Để Chọn Nhiệm Vụ : ")
        list_nv = list(settings["nhiemvu"]) if settings["nhiemvu"] else []
        if not list_nv:
            print_rtv("[!] Không Chọn Jobs Sao Chạy Hả Thằng Ngu")
            sys.exit()
        while True:
            try:
                min_delay = int(input_rtv("[?] Nhập Delay Min : "))
                if min_delay < 0: continue
                break
            except: print_rtv("[!] Vui Lòng Nhập Số")
        while True:
            try:
                max_delay = int(input_rtv("[?] Nhập Delay Max : "))
                if max_delay < min_delay: continue
                break
            except: print_rtv("[!] Vui Lòng Nhập Số")
        settings["delay"] = (min_delay, max_delay)
        while True:
            try:
                settings["JobbBlock"] = int(input_rtv("[?] Sau Bao Nhiêu Jobs Thì Chống Block : "))
                if settings["JobbBlock"] <= 1: continue
                break
            except: print_rtv("[!] Vui Lòng Nhập Số")
        while True:
            try:
                settings["DelayBlock"] = int(input_rtv(f"[?] Sau {settings['JobbBlock']} Jobs Nghỉ Bao Nhiêu Giây : "))
                break
            except: print_rtv("[!] Vui Lòng Nhập Số")
        while True:
            try:
                settings["JobBreak"] = int(input_rtv("[?] Sau Bao Nhiêu Jobs Thì Chuyển Page : "))
                if settings["JobBreak"] <= 1: continue
                break
            except: print_rtv("[!] Vui Lòng Nhập Số")
        settings["autoch"] = "n"
        settings["runidfb"] = input_rtv("[?] Bạn Có Muốn Ẩn UID Page [ y / n ] : ")
        with open(setting_file, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4)
else:
    settings = {}
    settings["nhiemvu"] = input_rtv("[?] Nhập Số Để Chọn Nhiệm Vụ : ")
    list_nv = list(settings["nhiemvu"]) if settings["nhiemvu"] else []
    if not list_nv:
        print_rtv("[!] Không Chọn Jobs Sao Chạy Hả Thằng Ngu")
        sys.exit()
    while True:
        try:
            min_delay = int(input_rtv("[?] Nhập Delay Min : "))
            if min_delay < 0: continue
            break
        except: print_rtv("[!] Vui Lòng Nhập Số")
    while True:
        try:
            max_delay = int(input_rtv("[?] Nhập Delay Max : "))
            if max_delay < min_delay: continue
            break
        except: print_rtv("[!] Vui Lòng Nhập Số")
    settings["delay"] = (min_delay, max_delay)
    while True:
        try:
            settings["JobbBlock"] = int(input_rtv("[?] Sau Bao Nhiêu Jobs Thì Chống Block : "))
            if settings["JobbBlock"] <= 1: continue
            break
        except: print_rtv("[!] Vui Lòng Nhập Số")
    while True:
        try:
            settings["DelayBlock"] = int(input_rtv(f"[?] Sau {settings['JobbBlock']} Jobs Nghỉ Bao Nhiêu Giây : "))
            break
        except: print_rtv("[!] Vui Lòng Nhập Số")
    while True:
        try:
            settings["JobBreak"] = int(input_rtv("[?] Sau Bao Nhiêu Jobs Thì Chuyển Page : "))
            if settings["JobBreak"] <= 1: continue
            break
        except: print_rtv("[!] Vui Lòng Nhập Số")
    settings["autoch"] = "n"
    settings["runidfb"] = input_rtv("[?] Bạn Có Muốn Ẩn UID Page [ y / n ] : ")
    with open(setting_file, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

proxy_main = proxy_list[0] if proxy_list else None
ttc = TuongTacCheo(token, proxy_main)

total_cookies_global = len(listCookie)
totalxu_lock = {'value': 0}
stt_lock = {'value': 0}
max_workers = min(len(listCookie), 10)
print_rtv(f"[✓] Bắt đầu chạy đa luồng với {max_workers} luồng...")
thanhngang(65)

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = []
    for idx, cookie in enumerate(listCookie):
        proxy = proxy_list[idx % len(proxy_list)] if proxy_list else None
        futures.append(executor.submit(process_cookie, ttc, cookie, proxy, settings, list_nv, totalxu_lock, stt_lock))
    for future in as_completed(futures):
        future.result()

print_rtv("\n[✓] Hoàn tất tất cả cookie.")
