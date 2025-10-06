//Copyright (c) [2023] [JinCanQi]
//[make_data_set_so-vits-svc] is licensed under Mulan PubL v2.
//You can use this software according to the terms and conditions of the Mulan PubL v2.
//You may obtain a copy of Mulan PubL v2 at:
//         http://license.coscl.org.cn/MulanPubL-2.0
//THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
//EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
//MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
//See the Mulan PubL v2 for more details.

package main

import (
	"flag"
	"log"
	"make_data_set_so-vits-svc/py/web_rtc/pion-to-pion/answer"
	"make_data_set_so-vits-svc/py/web_rtc/pion-to-pion/offer"
	"make_data_set_so-vits-svc/py/web_rtc/pion-to-pion/signal"
	"net/url"
	"os"
)

func main() {

	log.SetOutput(os.Stderr)

	// 获取命令行参数 判断是offer还是answer（必选其一） 获取信令服务器地址（必须）
	var isOffer bool
	var isAnswer bool
	var signalServerAddr string
	flag.BoolVar(&isOffer, "offer", false, "设置此标志以指示该程序是offer。")
	flag.BoolVar(&isAnswer, "answer", false, "设置此标志以指示该程序是answer。")
	flag.StringVar(&signalServerAddr, "signal-server", "", "要使用的信令服务器的地址，例如：http://localhost:8080。")
	flag.Parse()

	if !isOffer && !isAnswer {
		log.Panicln("请说明该程序是offer还是answer。")
	}
	if _, err := url.Parse(signalServerAddr); signalServerAddr == "" && err == nil {
		log.Panicln("请指定要使用的信令服务器正确的地址。")
	}

	if isOffer {
		log.Println("这是一个offer。")
	} else {
		log.Println("这是一个answer。")
	}
	log.Println("信令服务器地址：", signalServerAddr)

	signal.Adder = signalServerAddr
	if isOffer {
		signal.Now = signal.Offer
		offer.Offer()
	} else {
		signal.Now = signal.Answer
		answer.Answer()
	}
}
