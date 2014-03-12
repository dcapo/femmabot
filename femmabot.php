#!/usr/bin/php
<?php

class Util {
    public static function print_ln($message) {
        print($message . PHP_EOL);
    }
}

class BlogPost {
    protected $data;
    
    public function __construct($data) {
        $this->data = $data;
    }
    
    private static function get_response($url, $context) {
        $handle = curl_init();

        curl_setopt($handle, CURLOPT_URL, $url);
        curl_setopt($handle, CURLOPT_HEADER, false);
        curl_setopt($handle, CURLOPT_HTTPHEADER, array("Content-Type: text/xml"));
        curl_setopt($handle, CURLOPT_POSTFIELDS, $context);
        curl_setopt($handle, CURLOPT_RETURNTRANSFER, 1);

        $response = curl_exec($handle);
        curl_close($handle);
        return $response;
    }
    
    public static function get_recent_posts($blog_url, $username, $password, $count) {
       $request = xmlrpc_encode_request("metaWeblog.getRecentPosts",
                                        array('', $username, $password, $count));

       $xml = self::get_response($blog_url . "/xmlrpc.php", $request);
       return xmlrpc_decode($xml);
    }
    
    public static function get_post($blog_url, $post_id, $username, $password) {
       $request = xmlrpc_encode_request("metaWeblog.getPost",
                                        array($post_id, $username, $password));

       $xml = self::get_response($blog_url . "/xmlrpc.php", $request);
       return xmlrpc_decode($xml);
    }
    
    public function uploadImage() {
        
    }
    
    public function getBody() {
        $post = "<h1>{$self->data['h1']}</h1>$post<h3>{$self->data['h3']}</h3>";
        
        $keywords = str_replace(' ', '', $this->data['link_keywords']);
        foreach ($keywords as $keyword) {
            $anchor = "<a href='{$post->data['home_page']}' title='$keyword'>$keyword</a>";
            $post = str_replace($keyword, $anchor, $post);
        }
        
        return $post;
    }
    
    public function upload($publish) {
        
        $content = array(
            'title' => $this->data['title'],
            'description' => 'some things',
            'post_type' => 'post',
            'mt_allow_comments'=> 'closed',
            'mt_allow_pings'=> 'closed',
            'custom_fields' => array(
                array(
                    'key' => '_aioseop_description',
                    'value' => 'seo descriptioners'
                ),
                array(
                    'key' => '_aioseop_keywords',
                    'value' => 'seo,keywords,ha'
                ),
                array(
                    'key' => '_aioseop_title',
                    'value' => 'seo title yaya'
                )
            )
        );
        
        $request_data = array('', $this->data['username'], $this->data['password'],
                              $content, $publish);
        $request = xmlrpc_encode_request("metaWeblog.newPost", $request_data);
        $xml = get_response($blog_url . "/xmlrpc.php", $request);
        return xmlrpc_decode($xml);
    }
}

class TsvReader {
    protected $tsv_file;
    
    public function __construct($tsv_file) {
        $this->tsv_file = $tsv_file;
        
        $tsv_regex = '/^\w+.tsv$/';
        if (!preg_match($tsv_regex, $tsv_file)) {
            throw new Exception("Uh oh! $tsv_file doesn't look like a TSV file.");
        }
    }
    
    public static function validate($blog_post_data) {
        $required_keys = array('url', 'username', 'password');
        foreach ($required_keys as $i => $key) {
            if (!isset($blog_post_data[$key]) || empty($blog_post_data[$key])) {
                throw new Exception("Whoops! Looks like there isn't a value for the " + $key + " column in row " + $i + ".");
            }
        }
    }
    
    public function read() {
        $this->validate();
        $handle = fopen("inputfile.txt", "r");
        if ($handle) {
            $output = array();
            $i = 0;
            while (($line = fgets($handle)) !== false) {
                if ($i === 0) {
                    $columns = split('    ', $line);
                } else {
                    $blog_post_data = array_combine($columns, split('    ', $line));
                    if ($blog_post_data === false) {
                        $line_number = $i + 1;
                        throw new Exception("Oh no! There are a different number of \
                                             columns for line $line_number.");
                    }
                    self::validate($blog_post_data);
                    $output[] = $blog_post_data;
                }
                $i++;
            }
        } else {
            throw new Exception("Error reading file $this->tsv_file");
        }
    }
    
}

if (!(count($argv) > 2)) {
    Util::print_ln("Whoops! Remember to include the paths of both the \
                    clients and blog posts TSV files.");
    exit;
}

try {
    $clients_tsv_reader = new TsvReader($argv[1]);
    $clients = $clients_tsv_reader->read();
    
    $blog_posts_tsv_reader = new TsvReader($argv[2]);
    $blog_posts = $blog_posts_tsv_reader->read();
    
    foreach ($blog_posts as $line_data) {
        $blog_url = $line_data['url'];
        if (!isset($clients[$blog_url])) {
            throw new Exception("Oops! Couldn't find client info for the blog $blog_url");
        }
        $client_data = $clients[$line_data['url']];
        $line_data = array_merge($line_data, $client_data);
        $blog_post= new BlogPost($line_data);
        $blog_post->upload(false);
    }
} catch (Exception $e) {
    Util::print_ln($e->getMessage);
    exit;
}

?>