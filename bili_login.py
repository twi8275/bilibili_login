import time
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


username="用户名"
password="密码"
MULTIPE = 1.25  # 显示比例，我这里是125%
BORDER = 6

class CrackBili():
    def __init__(self):
        self.url = 'https://passport.bilibili.com/login'
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 10)

    # 程序完成，自动结束程序
    def __del__(self):
        self.browser.close()

    def open(self):
        """
        打开网页
        :return: None
        """
        self.browser.get(self.url)
        # self.browser.maximize_window()

    def get_position(self):
        """
        获取验证码位置
        :return: 验证码位置元组
        """
        img = self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'geetest_window')))
        print('img')
        location = img.location
        print(location)
        size = img.size
        top, bottom, left, right = location['y'], location['y'] + size['height'], location['x'], location['x'] + size['width']
        return (top, bottom, left, right)

    def get_screenshot(self):
        """
        获取网页截图
        :return: 截图对象
        """
        screenshot = self.browser.get_screenshot_as_png()
        screenshot = Image.open(BytesIO(screenshot))
        return screenshot

    def get_slider(self):
        """
        获取滑块
        :return: 滑块对象
        """
        slider = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'geetest_slider_button')))
        return slider

    def get_geetest_image(self, name='captcha.png'):
        """
        获取验证码图片
        :return: 图片对象
        """
        top, bottom, left, right = self.get_position()
        print('验证码位置', top, bottom, left, right)
        screenshot = self.get_screenshot()
        captcha = screenshot.crop(map(lambda x: int(x * MULTIPE), (left, top, right, bottom)))
        captcha.save(name)
        return captcha

    def delete_style(self):
        '''
        执行js脚本，获取无滑块图
        :return None
        '''
        js = 'document.querySelectorAll("canvas")[3].style=""'
        self.browser.execute_script(js)

    def get_gap(self, image1, image2):
        """
        获取缺口偏移量
        :param image1: 带缺口图片
        :param image2: 不带缺口图片
        :return:
        """
        left = int(60 * MULTIPE)  # 滑块最右测在验证码图片上的x坐标为60
        print(image1.size)
        print(image1.size[0])
        print(image1.size[1])
        for i in range(left, image1.size[0]):
            for j in range(image1.size[1]):
                if not self.is_pixel_equal(image1, image2, i, j):
                    left = i
                    return left
        return left

    def is_pixel_equal(self, image1, image2, x, y):
        """
        判断两个像素是否相同
        :param image1: 图片1
        :param image2: 图片2
        :param x: 位置x
        :param y: 位置y
        :return: 像素是否相同
        """
        # 取两个图片的像素点
        pixel1 = image1.load()[x, y]
        pixel2 = image2.load()[x, y]
        threshold = 60
        if abs(pixel1[0] - pixel2[0]) < threshold and abs(pixel1[1] - pixel2[1]) < threshold and abs(
                pixel1[2] - pixel2[2]) < threshold:
            return True
        else:
            return False

    def get_track(self, distance):
        """
        根据偏移量获取移动轨迹
        :param distance: 偏移量
        :return: 移动轨迹
        """
        # 移动轨迹
        track = []
        # 当前位移
        current = 0
        # 减速阈值
        mid = distance * 4 / 5
        # 计算间隔
        t = 0.2
        # 初速度
        v = 0
        while current < distance:
            if current < mid:
                # 加速度为正2
                a = 2
            else:
                # 加速度为负3
                a = -1
            # 初速度v0
            v0 = v
            # 当前速度v = v0 + at
            v = v0 + a * t
            # 移动距离x = v0t + 1/2 * a * t^2
            move = v0 * t + 1 / 2 * a * t * t
            # 当前位移
            current += move
            # 加入轨迹
            track.append(round(move))
        return track

    def move_to_gap(self, slider, track):
        """
        拖动滑块到缺口处
        :param slider: 滑块
        :param track: 轨迹
        :return:
        """
        ActionChains(self.browser).click_and_hold(slider).perform()
        for x in track:
            ActionChains(self.browser).move_by_offset(xoffset=x, yoffset=0).perform()
        time.sleep(0.5)
        ActionChains(self.browser).release().perform()

    def wait_pic(self):
        '''
        等待验证图片加载完成
        :return None
        '''
        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR,'.geetest_panel_box'))
        )

    def login(self):
        try:
            self.open()
            username_ele = self.browser.find_element_by_xpath("//input[@id='login-username']")
            password_ele = self.browser.find_element_by_xpath("//input[@id='login-passwd']")
            username_ele.send_keys(username)
            time.sleep(1)
            password_ele.send_keys(password)
            time.sleep(2)
            submit_btn = self.browser.find_element_by_xpath("//a[@class='btn btn-login']")
            submit_btn.click()
            time.sleep(2)
            # 确认图片加载完成
            self.wait_pic()
            # 获取滑块
            slider = self.get_slider()
            # 获取带缺口验证码图片
            image1 = self.get_geetest_image('captcha1.png')
            # 获取不带缺口的验证码图片
            self.delete_style()
            image2 = self.get_geetest_image('captcha2.png')
            # 获取缺口位置
            gap = self.get_gap(image2, image1)
            gap = int(gap / MULTIPE)
            print('缺口位置', gap)
            # 减去缺口位移
            gap -= BORDER
            # 获取移动轨迹
            track = self.get_track(gap)
            print('滑动轨迹', track)
            time.sleep(1)
            # 拖动滑块
            self.move_to_gap(slider, track)
            success = self.wait.until(
                EC.text_to_be_present_in_element((By.CLASS_NAME, 'nav-name'), '首页')
            )
            print(success)
            time.sleep(1)
        except:
            print('失败，再来一次')
            self.login()



if __name__=="__main__":
    crack=CrackBili()
    crack.login()