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
	"fmt"
	"make_data_set_so-vits-svc/download"
	"make_data_set_so-vits-svc/parse"
	"time"
)

const siftTime = 2022

func main() {
	sift, err := parse.KuGouParse.SiftByTime(time.Date(siftTime, 1, 1, 0, 0, 0, 0, time.Local), parse.KuGouModel)
	if err != nil {
		panic(err)
	}
	err = download.Download(sift)
	if err != nil {
		panic(err)
	}

	for _, v := range parse.GetMultipleVoices(sift) {
		fmt.Println("多说话人：", v)
	}

	// // 消除_(Vocals)后缀
	// err = tool.PlaceFilesWithTheSameNameAsFolderAAndFolderBInFolderC("./data/source/kugouRenSheng", "./data/source/kugou", "./data/source/c")
	// if err != nil {
	// 	panic(err)
	// }

	// num := 1
	// for _, v := range parse.KuGouParse.Search("Melody", sift) {
	// 	for _, vv := range v.Data {
	// 		fmt.Printf("%d-%d-%s-%s%s", num, download.GetAge(vv.PublishDate), vv.PublishDate, download.Sanitize(vv.AudioName), filepath.Ext("link.mp3"))
	// 		num++
	// 	}
	// }
}
