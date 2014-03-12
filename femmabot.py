import sys
import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import TimeoutException

class BlogPostException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return repr(self.message)
        
class WordPressDriver:
    IMAGE_MACRO = "MUSTAFA"
    IMAGE_DIR = '/Users/Daniel/Desktop'
    
    def __init__(self, driver, blog_post):
        self.driver = driver
        self.bp = blog_post
    
    def wait_until(self, expectation, error_message=None):
        try:
            WebDriverWait(self.driver, 10).until(expectation)
        except TimeoutException:
            if error_message:
                raise AssertionError(error_message)
    
    def login(self):
        self.driver.get(self.bp['url'] + '/wp-login.php')
        username_input = self.driver.find_element_by_name("log")
        username_input.send_keys(self.bp['username'])
        password_input = self.driver.find_element_by_name("pwd")
        password_input.send_keys(self.bp['password'])
        log_in_button = self.driver.find_element_by_name("wp-submit")
        log_in_button.click()
        assert 'Dashboard' in self.driver.title, 'failed to login to %s.' % self.bp['url']
    
    def update_plugins(self):
        pass
        
    def complete_image_form(self, attachment_details):
        title_input = attachment_details.find_element_by_xpath("//label[@data-setting='title']/input")
        title_input.clear()
        title_input.send_keys(self.bp['image_caption'])
        
        caption_input = attachment_details.find_element_by_xpath("//label[@data-setting='caption']/textarea")
        caption_input.send_keys(self.bp['image_caption'])
        
        alt_text_input = attachment_details.find_element_by_xpath("//label[@data-setting='alt']/input")
        alt_text_input.send_keys(self.bp['image_caption'])
        
        description_input = attachment_details.find_element_by_xpath("//label[@data-setting='description']/textarea")
        description_input.send_keys(self.bp['image_description'] + '\n' + self.bp['address'])
        
        alignment_select = attachment_details.find_element_by_xpath("//select[@data-setting='align']")
        Select(alignment_select).select_by_value(self.bp['image_alignment'].lower())
        
    def upload_image(self):
        media_button = self.driver.find_element_by_id("insert-media-button")
        media_button.click()
        
        media_modal = self.driver.find_element_by_class_name("media-modal")
        assert media_modal.is_displayed(), 'media modal did not become visible.'
        
        upload_files_link = self.driver.find_element_by_class_name("media-modal").find_element_by_link_text("Upload Files")
        upload_files_link.click()
        upload_ui = media_modal.find_element_by_class_name("upload-ui")
        assert upload_ui.is_displayed(), 'file upload UI did not become visible.'
        
        file_input = media_modal.find_element_by_css_selector(".plupload input")
        file_input.send_keys("%s/%s" % (WordPressDriver.IMAGE_DIR, self.bp['image_name']))
        
        expectation = EC.invisibility_of_element_located((By.CSS_SELECTOR, ".media-sidebar .media-uploader-status"))
        self.wait_until(expectation)
        
        error_dialog = media_modal.find_element_by_class_name("upload-errors")
        assert not error_dialog.is_displayed(), 'image file upload failed.'
        
        attachment_details = media_modal.find_element_by_class_name("attachment-details")
        self.complete_image_form(attachment_details)
        
        insert_button = media_modal.find_element_by_css_selector(".media-toolbar .media-button-insert")
        assert insert_button.is_enabled(), 'image file could not be inserted into post.'
        insert_button.click()
        
        expectation = EC.text_to_be_present_in_element_value((By.ID,'content'), '%s[/caption]' % self.bp['image_caption'])
        self.wait_until(expectation, "image HTML never got inserted into the post content.")
    
    def insert_post_body(self):
        text_tab = self.driver.find_element_by_id("content-html")
        text_tab.click()
        
        content = self.driver.find_element_by_id("content")
        h1 = "<h1>%s</h1>" % self.bp['h1']
        h3 = "<h3>%s \n %s</h3>" % (self.bp['h3'], self.bp['address'])
        post = "%s\n%s\n%s" % (h1, self.bp['body'], h3)
        keywords = self.bp['link_keywords'].replace(' ', '').split(',')
        for keyword in keywords:
            post = post.replace(keyword, "<a href='%s' title='%s'>%s</a>" % (self.bp['home_page'], keyword, keyword))
        post_sections = post.split(WordPressDriver.IMAGE_MACRO)
        if len(post_sections) == 1:
            content.send_keys(post_sections[0])
        elif len(post_sections) == 2:
            content.send_keys(post_sections[0])
            self.upload_image()
            content.send_keys(post_sections[1])
        else:
            raise AssertionError('Oh no! Too many image macros.')
    
    def complete_seo_form(self):
        assert len(self.driver.find_elements_by_css_selector("#aiosp")), 'no SEO pack.'
        seo_form = self.driver.find_element_by_id("aiosp")
        
        title_input = seo_form.find_element_by_name("aiosp_title")
        title_input.send_keys("%s | %s" % (self.bp['title'], self.bp['h1']))
        
        description_input = seo_form.find_element_by_name("aiosp_description")
        description_input.send_keys(self.bp['seo_description'])
        
        keywords = seo_form.find_element_by_name("aiosp_keywords")
        keywords.send_keys(self.bp['seo_keywords'])
        
    def choose_category(self):
        category_list = self.driver.find_element_by_id("categorychecklist")
        x_path = "//label[@class='selectit' and text()=' %s']" % self.bp['category']
        category_checkbox = category_list.find_elements_by_xpath(x_path)
        if len(category_checkbox):
            category_checkbox[0].find_element_by_css_selector("input").click()
        else:
            category_add_toggle = self.driver.find_element_by_id("category-add-toggle")
            category_add_toggle.click()
            
            category_input = self.driver.find_element_by_id("newcategory")
            category_input.send_keys(self.bp['category'])
            category_submit_button = self.driver.find_element_by_id("category-add-submit")
            category_submit_button.click()
        
    def create_blog_post(self, publish):
        posts_button = self.driver.find_element_by_id("wp-admin-bar-new-content")
        posts_button.click()
        assert 'Add New Post' in self.driver.title, 'failed to reach the New Post page.'
        
        title_input = self.driver.find_element_by_name("post_title") 
        title_input.send_keys(self.bp['title'])
        
        self.insert_post_body()
        self.complete_seo_form()
        self.choose_category()
        
        tags_input = self.driver.find_element_by_id("new-tag-post_tag")
        tags_input.send_keys(self.bp['seo_keywords'])
        
        self.driver.execute_script("document.body.scrollTop = document.documentElement.scrollTop = 0;")
        if publish:
            publish_button = self.driver.find_element_by_id("publish")
            publish_button.click()
            
            expectation = EC.text_to_be_present_in_element((By.ID,'message'), "Post published.")
            self.wait_until(expectation, "post failed to publish.")
        else:
            save_button = self.driver.find_element_by_id("save-post")
            save_button.click()
            
            expectation = EC.text_to_be_present_in_element((By.ID,'message'), "Post draft updated.")
            self.wait_until(expectation, "post failed to save.")
        
        anchor = self.driver.find_element_by_css_selector("#message p a")
        return anchor.get_attribute('href')
                
    
    def judo_chop(self):
        self.login()
        self.update_plugins()
        return self.create_blog_post(False)

class TsvReader:
    def __init__(self, tsv):
        self.tsv = tsv
        
    def read(self, required_keys):
        file_handle = open(self.tsv, 'r')
        output = []
        for i, line in enumerate(file_handle):
            if i == 0:
                columns = line.strip().split('    ');
            else:
                line_data = dict(zip(columns, line.split('    ')))
                for key in required_keys:
                    if not key in line_data or not line_data[key]:
                        raise BlogPostException("Whoops! Looks like there isn't a value for the '%s' column in row %i of %s." % 
                        (key, i, self.tsv))
                output.append(line_data)
        return output

class Femmabot:
    def __init__(self, clients_tsv, blog_posts_tsv):
        self.clients_tsv = clients_tsv
        self.blog_posts_tsv = blog_posts_tsv
    
    def merge_tsv_data(self, clients, blog_post):
        blog_url = blog_post['url']
        
        for client_i in clients:
            if client_i['url'] == blog_url:
                client = client_i
                break
        assert client, "Oops! Couldn't find client info for the blog %s" % blog_url
        
        return dict(client.items() + blog_post.items())
        
    def arm_the_probe(self):
        try:
            required_client_keys = ['url', 'username', 'password', 'address', 'home_page']
            clients = TsvReader(self.clients_tsv).read(required_client_keys)
            
            required_blog_post_keys = ['url', 'title', 'h1', 'body', 'h3', 'link_keywords', 
                                       'image_name', 'image_caption', 'image_description', 
                                       'image_alignment', 'seo_description', 'seo_keywords',
                                       'category']
            blog_posts = TsvReader(self.blog_posts_tsv).read(required_blog_post_keys)
            
            driver = webdriver.Chrome()
            driver.maximize_window()
            for i, blog_post in enumerate(blog_posts):
                try:
                    print "%i." % (i + 1),
                    blog_post = self.merge_tsv_data(clients, blog_post)
                    word_press_driver = WordPressDriver(driver, blog_post)
                    post_url = word_press_driver.judo_chop()
                    print "PASS: %s" % post_url
                except AssertionError as e:
                    print "ERROR: %s" % e
                except:
                    print "ERROR: %s" % sys.exc_info()[0]
                    raise
                    break
        except BlogPostException as e:
            print e.message
        finally:
            if 'driver' in locals():
                pass# driver.close()

if not len(sys.argv) > 2: 
    print("Whoops! Remember to include the paths of both the clients and blog posts TSV files.")
    sys.exit()
clients_tsv = sys.argv[1]
blog_posts_tsv = sys.argv[2]
tsv_re = '^\w+.tsv$'
if not re.match(tsv_re, clients_tsv) or not re.match(tsv_re, blog_posts_tsv):
    print "Oh no! Femmabot only accepts TSV files."
    sys.exit()

femmabot = Femmabot(clients_tsv, blog_posts_tsv)
femmabot.arm_the_probe()