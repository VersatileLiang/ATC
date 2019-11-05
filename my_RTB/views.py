from django.shortcuts import render
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time
from multiprocessing import Pool
import threading
import _thread
import glob
import os
import shutil
import string
import zipfile

# Create your views here.
def index(request):
    return render(request, 'index.html')


class myThread (threading.Thread):
    def __init__(self, threadID, name, threadCount, commodityURL, size, ip_agent):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.threadCount = threadCount
        self.commodityURL = commodityURL
        self.size = size
        self.ip_agent = ip_agent
    def run(self):
        set_log(self.name + "开始")
        main_buy(self.name, self.threadCount, self.commodityURL, self.size, self.ip_agent)
        set_log(self.name + "退出")

# 登录
def white_login(username, password, browser):
    # 打开登录页
    browser.get('https://www.off---white.com/en/IT/login')
    # WebDriverWait(browser, 10, 0.25).until(browser.find_element_by_id("spree_user_email"))
    # 填写登录信息：用户名、密码
    try:
        browser.find_element_by_id("spree_user_email").send_keys(username)
    except:
        return "访问失败，可能是IP被封，请切换重试"
    browser.find_element_by_id("spree_user_password").send_keys(password)
    time.sleep(1)
    # 点击登录
    browser.find_element_by_name("commit").click()
    time.sleep(1)
    return "登录成功"

# 抢购
def post_white(browser, commodityURL, size):
    try:
        browser.get(commodityURL)
    except:
        return "输入的网址有误"
    time.sleep(2)
    if size != "0":
        size = "variant_id_" + size
        try:
            sml = browser.find_element_by_id(size).click()
            time.sleep(2)
        except:
            return "当前尺寸暂时缺货"
    # WebDriverWait(browser, 10, 0.25).until(browser.find_element_by_class_name("product-cart-form"))
    try:
        post_button = browser.find_element_by_class_name("product-cart-form").submit()
    except:
        return "尝试失败，即将进入下次..."
    time.sleep(3)
    try:
        browser.find_element_by_class_name("added")
    except:
        try:
            browser.find_element_by_class_name("quantity")
        except:
            return "失败"
        return "相同商品超过数量限制，请勿购买太多"
    return "成功"

# 抢购主函数
def main_buy(_threadName, threadCount, commodityURL, size, ip_agent):
    ip_list = ip_agent.split("\r\n")
    for list in ip_list:
        option = webdriver.ChromeOptions()  # 实例化一个ChromeOptions对象
        ipecl = list.split(":")
        proxyHost = ipecl[0]
        if proxyHost != "0":
            try:
                proxyPort = ipecl[1]
                proxyUser = ipecl[2]
                proxyPass = ipecl[3]
                proxy_auth_plugin_path = create_proxy_auth_extension(
                    proxy_host=proxyHost,
                    proxy_port=proxyPort,
                    proxy_username=proxyUser,
                    proxy_password=proxyPass)
                option.add_extension(proxy_auth_plugin_path)  # 使用代理
            except:
                set_log(_threadName + "输入的代理ip格式错误")
                set_log(_threadName + "准备尝试下一个ip代理......")
        option.add_argument("--start-maximized")
        option.add_experimental_option('excludeSwitches', ['enable-automation'])  # 以键值对的形式加入参数
        option.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2,
                                                 'permissions.default.stylesheet': 2})  # 处理图片和css
        # option.add_argument('--headless') # 设置隐藏浏览器执行操作 生产环境打开可能有bug，需要调试
        # 设置chromedriver路径
        executable_path = os.getcwd() + '\my_RTB\chromedriver.exe'
        # 设置用户名、密码
        username = 'alex@4nnulled.com'
        password = "q1w2e3"
        # desired_capabilities = DesiredCapabilities.CHROME
        # desired_capabilities["pageLoadStrategy"] = "none"
        browser = webdriver.Chrome(executable_path=executable_path, options=option)
        # browser.set_page_load_timeout(3) #设定加载等待时间
        browser.implicitly_wait(1.5)  # 设定完成等待时间
        info = white_login(username, password, browser)
        log = _threadName + info
        set_log(log)
        if info == '访问失败，可能是IP被封，请切换重试':
            browser.close()
            set_log(_threadName + "正在切换ip代理......")
            set_log(_threadName + "正在重启浏览器......")
            continue
        size_list = size.split()
        size_count = 0
        for size in size_list:
            size_count += 1
            count = 0
            while 1:
                result = post_white(browser, commodityURL, size)
                count += 1
                if size == "0":
                    set_log(_threadName + "第" + str(count) + "次尝试结果：" + result)
                else:
                    set_log(_threadName + "第" + str(size_count) + "个尺寸：" + size + "-" + "第" + str(
                        count) + "次尝试结果：" + result)
                if result == "成功":
                    browser.close()
                    break
                elif result == "相同商品超过数量限制，请勿购买太多":
                    browser.close()
                    break
                elif result == "当前尺寸暂时缺货":
                    browser.close()
                    break
                elif result == "输入的网址有误":
                    browser.close()
                    break
                if count >= threadCount:
                    log = _threadName + "尝试次数过多，该尺寸结束"
                    set_log(log)
                    break
        set_log(_threadName + "全部尺寸尝试结束，该线程结束")
        return 0
    set_log(_threadName + "以上代理全部失效，请尝试输入新的代理！")

# 抢购
def RTB(request):
    path = os.getcwd() + '/my_RTB/log' + '/' + 'log'
    try:
        shutil.rmtree(path) # 清理日志
    except Exception :
        print('日志不存在')
    set_log("主线程开始")
    # 使用多线程
    threadList = []
    # 线程数量
    threadNumber = int(request.POST['number'])
    # 单个线程尝试次数
    threadCount = int(request.POST['count'])
    # 需要购买的商品的网址
    commodityURL = request.POST['dataOrigin']
    # commodityURL = "https://www.off---white.com/en/IT/men/products/omec008e198060051088#"
    # 尺寸编号
    size = request.POST['size']
    # ip代理
    ip_agent = request.POST['ip_agent']
    # 创建新线程
    i = 1
    while i <= threadNumber:
        thread = myThread(i, "线程" + str(i) + "-", threadCount, commodityURL, size, ip_agent)
        threadList.append(thread)
        i += 1
        thread.start()
        time.sleep(5)

    for thread in threadList:
        thread.join()

    log_info = "退出主线程"
    set_log(log_info)
    path = os.getcwd() + '/my_RTB/log' + '/' + 'log'
    file_list = get_file_count(path, '.log')['filenames']
    # print(file_list)
    return render(request, 'index.html',
                  {
                      'log_list': file_list
                  }
                  )

# 记录日志
def set_log(info):
    print(info)
    datetime = time.strftime('%Y.%m.%d', time.localtime(time.time()))
    time1 = time.strftime('%Y.%m.%d-%H.%M.%S', time.localtime(time.time()))
    path = os.getcwd() + '/my_RTB/log' + '/' + 'log' + '-' + datetime + '/'
    path2 = os.getcwd() + '/my_RTB/log' + '/' + 'log' + '/'
    if os.path.exists(path) == 0:
        os.makedirs(path)
    os.path.exists(path)
    if os.path.exists(path2) == 0:
        os.makedirs(path2)
    os.path.exists(path2)
    path_file = get_file_count(path, '.log')
    count = path_file['counts']  # 获取指定路径下有多少文件
    if count < 10:
        str_count = '000' + str(count)
    elif count < 100:
        str_count = '00' + str(count)
    elif count < 1000:
        str_count = '0' + str(count)
    else:
        str_count = str(count)
    f = open(path + '/' + str_count + '-' + time1 + '-' + info + '.log', 'a', encoding='utf-8')
    f.close()

    path_file = get_file_count(path2, '.log')
    count = path_file['counts']  # 获取指定路径下有多少文件
    if count < 10:
        str_count = '000' + str(count)
    elif count < 100:
        str_count = '00' + str(count)
    elif count < 1000:
        str_count = '0' + str(count)
    else:
        str_count = str(count)
    f = open(path2 + '/' + str_count + '-' + time1 + '-' + info + '.log', 'a', encoding='utf-8')
    f.close()

# 获取某路径下某扩展名的详情信息(文件个数和文件名)
def get_file_count(path, type):
    """
    :param path: 文件夹路径
    :param type: 文件扩展名
    :return: 返回一个字典，counts表示文件个数，filenames表示所有文件的文件名
    """
    import os.path
    dir = path
    m = 0
    files = []
    for parentdir, dirname, filenames in os.walk(dir):
        for filename in filenames:
            # print(filename)
            files.append(filename)
            if os.path.splitext(filename)[1] == type:
                m = m + 1
    # print(m)
    return {'counts': m, 'filenames': files}

def get_log(request):
    path = os.getcwd() + '/my_RTB/log' + '/' + 'log'
    file_list = get_file_count(path, '.log')['filenames']
    print(file_list)
    return render(request, 'index.html',
                  {
                      'log_list': file_list
                  }
                  )

def get_size(request):
    return render(request, 'size.html')

def create_proxy_auth_extension(proxy_host, proxy_port,
                               proxy_username, proxy_password,
                               scheme='http', plugin_path=None):
    if plugin_path is None:
        plugin_path = r'' + os.getcwd() + '/my_RTB/ip_list/{}_{}.zip'.format(proxy_username, proxy_password)

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Abuyun Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = string.Template(
        """
        var config = {
            mode: "fixed_servers",
            rules: {
                singleProxy: {
                    scheme: "${scheme}",
                    host: "${host}",
                    port: parseInt(${port})
                },
                bypassList: ["foobar.com"]
            }
          };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "${username}",
                    password: "${password}"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {urls: ["<all_urls>"]},
            ['blocking']
        );
        """
    ).substitute(
        host=proxy_host,
        port=proxy_port,
        username=proxy_username,
        password=proxy_password,
        scheme=scheme,
    )

    with zipfile.ZipFile(plugin_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_path
#注释
