
import re
import os
import json
import requests
from pyquery import PyQuery as PQ

class Bilibili:

    def __init__(self):
        """请修改下载地址"""
        # 下载地址
        self.path = r"F:\spdiers\Bilbili\data"

        self.headers = {'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
        self.down_headers = {'Accept': '*/*','Accept-Encoding': 'identity','Accept-Language': 'zh-CN,zh;q=0.9','Connection': 'keep-alive','Host': 'upos-sz-mirrorcos.bilivideo.com','If-Range': '5e14e342-4a339e2','Origin': 'https://www.bilibili.com','Range': 'bytes=43477700-45364081','Referer': 'https://www.bilibili.com/video/av82508014?spm_id_from=333.851.b_7265706f7274466972737431.14','Sec-Fetch-Mode': 'cors','Sec-Fetch-Site': 'cross-site','User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36'}

        if not os.path.exists(self.path):
            os.makedirs("./videos")
            self.path = "./videos"

    def get_downurl(self,url):
        """
        提取视频的标题、视频和音频所在的url
        :param url: 视频所在页面的url
        :return: 视频标题、视频url、音频url
        """
        # 提取标题、url所在script脚本的url
        reg_title = re.compile('<title[\s\S]*?>([\s\S]*?)</title>')
        reg_script = re.compile('<script>window.__playinfo__=([\s\S]*?)</script>')
        response = requests.get(url=url, headers=self.headers)
        title = reg_title.findall(response.text)[0].replace("_哔哩哔哩 (゜-゜)つロ 干杯~-bilibili","").replace("/","-")
        script = reg_script.findall(response.text)[0]
        data = json.loads(script)
        video_url = data['data']['dash']['video'][0]['baseUrl']
        audio_url = data['data']['dash']['audio'][0]['base_url']
        print(title)
        # print(video_url)
        # print(audio_url)
        return title, video_url, audio_url

    def download(self,url, filename):
        """
        下载视频的执行函数
        :param url:     视频或音频url
        :param filename: 文件名
        :return:
        """
        print(f"down {url} start!")
        reg = re.compile(r"'Content-Length': '(\d+)'")
        # 每次下载 2M
        offest = 0                # 视频流位置
        const = 2048 * 1000       # 每次下载的视频流大小
        total = 0                 # 已下载的视频流大小
        last_offest = offest      # 上次下载的结束位置

        while True:
            offest += const       # 本次下载的结束位置
            self.down_headers['Range'] = "bytes={}-{}".format(last_offest,offest)
            response = requests.get(url=url,headers=self.down_headers,stream=True)
            rh = str(response.headers)
            content = reg.findall(rh)
            # 保存到本地
            with open(f"{self.path}/{filename}", "ab") as f:
                f.write(response.content)
            # 如果当前返回视频流大小小于要获取的，说明已到视频末尾
            if int(content[0]) < const:
                total += int(content[0])
                print("\r", "已下载{}MB".format(round(total / 1024 / 1024, 2)), end='')
                break
            # 更新位置
            last_offest = offest + 1
            total += const
            print("\r","已下载{}MB".format(round(total/1024/1024,2)), end='')

    def main(self, url):
        """
        下载视频的主函数，由于视频和音频是分开的，所以会下两次
        :param url: 视频所在页面的url
        :return:
        """
        title, video_url, audio_url = self.get_downurl(url)
        self.download(video_url, "{}.mp4".format(title))
        self.download(audio_url, "{}.mp3".format(title))

    def get_all_video(self, tier_limit = 3):
        """
        广度优先遍历，获取页面中所有的视频url
        :param tier_limit: 广度优先最大层数
        :return:    获取的urls
        """
        url = "https://www.bilibili.com/"              # 初始地址
        visited = [[url]]                              # 待访问的地址
        seen = set()                                   # 已访问过的集合
        current_tier = 0                               # 初始层数

        while True:
            # 如果已达最大层数，退出循环
            if current_tier == tier_limit:
                break
            urls = visited.pop()                       # 拿到一个url列表
            current_tier_urls = []                     # 当前层获取到的url列表

            # 开始遍历
            for url in urls:
                # 访问过则跳过
                if url in seen:
                    continue
                print(f"current url:{url}")
                seen.add(url)                         # 将url添加到已访问集合
                response = requests.get(url=url, headers=self.headers)
                # 提取页面中所有的a标签，筛选出所有是视频的url
                html = PQ(response.text)
                a_list = html("a")
                for a in a_list.items():
                    new_url = a.attr('href')
                    if new_url and new_url.startswith("/video/av"):
                        new_url = "https://www.bilibili.com" + new_url
                    elif new_url and new_url.startswith("//www.bilibili.com/video/av"):
                        new_url = "https:" + new_url
                    # 将url添加当前层的url列表
                    if new_url and new_url not in seen and new_url not in current_tier_urls and "video/av" in new_url:
                        current_tier_urls.append(new_url)

                print(f"after {url}:{current_tier_urls}")
            # 将新提取到的url放在前面就是广度优先
            visited = [current_tier_urls] + visited
            current_tier += 1                       # 层数 + 1
        return visited

if __name__ == '__main__':

    # 下载指定视频例子
    # url = "https://www.bilibili.com/video/av82761114?spm_id_from=333.851.b_7265706f7274466972737431.10"
    # b = Bilibili()
    # b.main(url)

    # 广度右下下载例子
    success = 0
    failed = 0
    b = Bilibili()
    urls = b.get_all_video(tier_limit=2)
    for url in urls[0]:
        try:
            b.main(url)
            success += 1
        except Exception as e:
            failed += 1
        print(f"下载成功 {success} 个，下载失败 {failed} 个！")


