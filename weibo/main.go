package main

import (
	"bufio"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/imroc/req"
)

var (
	Header = req.Header{
		"Cookie": "",
	}
	Uid = 0
)

type List struct {
	Text      string `json:"text"` // 此Text含有html标签
	TextRaw   string `json:"text_raw"`
	CreatedAt string `json:"created_at"` //Fri Oct 27 16:36:00 +0800 2023
	User      struct {
		Id int `json:"id"` //用此验证发布人
	} `json:"user"`
	PageInfo struct {
		PageTitle string `json:"page_title"`
	} `json:"page_info"` //如果 text为空则假设为生日动态，这个字段是生日动态的文本
	Id string `json:"id"`
}
type WenZhangRes struct {
	Data struct {
		List    []*List `json:"list"`
		ToTal   int     `json:"total"`
		SinceId int     `json:"since_id"`
	} `json:"data"`
}

func main() {
	// 打开文件，如果文件不存在则创建，以追加模式和写入模式打开
	file, err := os.OpenFile("weibo.txt", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		log.Panicln(err)
	}
	defer file.Close()

	// 创建一个 bufio.Writer
	writer := bufio.NewWriter(file)

	// 确保所有缓冲的数据都被写入到底层的 io.Writer 中
	defer writer.Flush()

	page := 1
	// 返回不定长的列表，第二页开始传递since_id
	sinceId := 0
	for {
		url2 := fmt.Sprintf("https://www.weibo.com/ajax/statuses/mymblog?uid=%d&page=%d&feature=0", Uid, page)
		if page > 1 {
			url2 += fmt.Sprintf("&since_id=%d", sinceId)
		}

		res, err := req.Get(url2, Header)
		if err != nil {
			log.Panicln(err)
		}
		var data WenZhangRes
		err = res.ToJSON(&data)
		if err != nil {
			log.Panicln(err)
		}

		//设置sinceId
		sinceId = data.Data.SinceId

		//判断为空则退出
		if len(data.Data.List) == 0 {
			log.Println("已经到底了")
			break
		}

		for _, v := range data.Data.List {
			// 判断发布人
			if v.User.Id != Uid {
				continue
			}

			// 使用 time.Parse 解析日期字符串
    		t, err := time.Parse(time.RubyDate, v.CreatedAt)
    		if err != nil {
    		    log.Panicln(err)
    		}

			text := ""
			//判断是否为生日动态
			if v.Text == ""{
				text = v.PageInfo.PageTitle
			}

			// 2006-01-02 15:04:05 Text
			_,err = fmt.Fprintf(writer, "%s %s",t.Format(time.DateTime),text)
			if err != nil {
				log.Panicln(err)
			}
		}

		page++
	}
}
