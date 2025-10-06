//Copyright (c) [2023] [JinCanQi]
//[make_data_set_so-vits-svc] is licensed under Mulan PubL v2.
//You can use this software according to the terms and conditions of the Mulan PubL v2.
//You may obtain a copy of Mulan PubL v2 at:
//         http://license.coscl.org.cn/MulanPubL-2.0
//THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
//EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
//MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
//See the Mulan PubL v2 for more details.

package parse

import (
	"encoding/json"
	"log"
	"make_data_set_so-vits-svc/config"
	"make_data_set_so-vits-svc/model"
	"os"
	"strings"
	"time"
)

var AuthorName = config.ConfigModel.AuthorName

var KuGouModel []*model.KuGouModel

type kuGouParse struct {
}

var KuGouParse = new(kuGouParse)

func init() {
	bytes, err := readFile(config.ConfigModel.KouGouJsonPathList)
	if err != nil {
		panic(err)
	}
	for _, v := range bytes {
		var kuGouModel model.KuGouModel
		err = json.Unmarshal(v, &kuGouModel)
		if err != nil {
			panic(err)
		}
		KuGouModel = append(KuGouModel, &kuGouModel)
	}
}

func readFile(filePath []string) (bytes [][]byte, err error) {
	for _, v := range filePath {
		data, err2 := os.ReadFile(v)
		err = err2
		if err != nil {
			return
		}
		bytes = append(bytes, data)
	}
	return
}

//这段代码定义了一个名为 SiftByTime 的方法，它接受两个参数：一个时间类型的变量 t 和一个 KuGouModel 类型的切片 kugouModel。
//该方法的作用是根据时间筛选 kugouModel 中的数据，将符合条件的数据存储到一个新的 KuGouModel 切片中并返回。
//具体实现是遍历 kugouModel 中的每个元素，对于每个元素，遍历其中的 Data 切片，如果其中的 PublishDate 字段表示的时间在 t 之后或等于 t，则将该元素添加到新的 KuGouModel 切片中。
//如果 PublishDate 字段为空，则会在日志中输出一条警告信息。
func (k *kuGouParse) SiftByTime(t time.Time, kugouModel []*model.KuGouModel) (result []*model.KuGouModel, err error) {
	for _, v := range kugouModel {
		newKuGouModel := &model.KuGouModel{
			Extra:     v.Extra,
			Data:      nil,
			Status:    v.Status,
			Errmsg:    v.Errmsg,
			Total:     v.Total,
			ErrorCode: v.ErrorCode,
		}
		for _, vv := range v.Data {
			if vv.PublishDate != "" {
				publishDate, err2 := time.ParseInLocation("2006-01-02", vv.PublishDate, time.Local)
				err = err2
				if err != nil {
					return
				}
				//此代码块使用 publishDate 变量来检查日期值是否在 t 变量中存储的日期之后。或者等于 t ，如果是，则 v 变量中的值将添加到结果变量中。
				if publishDate.After(t) || publishDate.Equal(t) {
					newKuGouModel.Data = append(newKuGouModel.Data, vv)
				}
			} else {
				log.Println("日期为空", vv.AudioName)
			}
		}
		result = append(result, newKuGouModel)
	}
	return
}

func GetMultipleVoices(kugouModel []*model.KuGouModel) (fileName []string) {
	for _, v := range kugouModel {
		for _, vv := range v.Data {
			if strings.TrimSpace(vv.AuthorName) != AuthorName {
				fileName = append(fileName, vv.AudioName)
			}
		}
	}
	return
}

// Search 按音乐名模糊搜索数据
func (k *kuGouParse) Search(name string, kugouModel []*model.KuGouModel) (result []*model.KuGouModel) {
	for _, v := range kugouModel {
		newKuGouModel := &model.KuGouModel{
			Extra:     v.Extra,
			Data:      nil,
			Status:    v.Status,
			Errmsg:    v.Errmsg,
			Total:     v.Total,
			ErrorCode: v.ErrorCode,
		}
		for _, vv := range v.Data {
			if strings.Contains(vv.AudioName, name) {
				newKuGouModel.Data = append(newKuGouModel.Data, vv)
			}
		}
		result = append(result, newKuGouModel)
	}
	return
}