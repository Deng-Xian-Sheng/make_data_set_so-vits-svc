//Copyright (c) [2023] [JinCanQi]
//[make_data_set_so-vits-svc] is licensed under Mulan PubL v2.
//You can use this software according to the terms and conditions of the Mulan PubL v2.
//You may obtain a copy of Mulan PubL v2 at:
//         http://license.coscl.org.cn/MulanPubL-2.0
//THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
//EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
//MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
//See the Mulan PubL v2 for more details.

package signal

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"time"

	signalCusterrors "signal-server/custerrors"
	signalModel "signal-server/model"

	webrtc "github.com/pion/webrtc/v3"
	"gopkg.in/yaml.v2"
)

var (
	Now, Adder, key string
)

const (
	Offer  = "offer"
	Answer = "answer"

	offerRoute  = "/offer"
	answerRoute = "/answer"

	keyTTL = int(30 * time.Second)
)

type config struct {
	PassWord string `yaml:"password"` // 用于信令交换的密码
}

var configModel = &config{}

func init() {
	refreshKey()
	go func() {
		for {
			time.Sleep(30 * time.Second)
			refreshKey()
		}
	}()
}

func refreshKey() {
	yamlFile, err := os.ReadFile("./config.yaml")
	if errors.Is(err, os.ErrNotExist) {
		out, err := yaml.Marshal(configModel)
		if err != nil {
			log.Panicln(err)
		}
		err = os.WriteFile("./config.yaml", out, os.ModePerm)
		if err != nil {
			log.Panicln(err)
		}
		log.Println("config.yaml文件不存在，已经创建，请填写配置")
		return
	}
	if err != nil {
		log.Panicln(err)
	}
	err = yaml.Unmarshal(yamlFile, configModel)
	if err != nil {
		log.Panicln(err)
	}

	// 判断当前时间的秒数，小于等于30则设为1，否则设为31
	second := 0
	if time.Now().Second() <= 30 {
		second = 1
	} else {
		second = 31
	}
	// 获取当前时间，自定义秒并将秒后面的单位置空，生成时间戳
	unix := time.Date(time.Now().Year(), time.Now().Month(), time.Now().Day(), time.Now().Hour(), time.Now().Minute(),
		second, 0, time.Local).Unix()
	// 将时间戳转化成a-z（可逆），并且与密码拼接，然后获取拼接后的字符串的sha256哈希
	hash := sha256.Sum256([]byte(strconv.FormatInt(unix, 10) + configModel.PassWord))
	// 恢复成字符串
	hashStr := hex.EncodeToString(hash[:])
	// 只获取32位
	key = hashStr[:32]
}

// 发送GET请求
func sendGetRequest(url string) ([]byte, error) {
	client := &http.Client{}
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Set("key", key)
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	res := &signalModel.GeneralRes{}
	err = json.Unmarshal(body, res)
	if err != nil {
		return nil, err
	}
	if res.Msg != "" {
		return nil, errors.New(res.Msg)
	}
	if res.Data == nil || res.Data.(string) == "" {
		return []byte{}, nil
	}
	return []byte(res.Data.(string)), nil
}

// 发送POST请求
func sendPostRequest(url string, body io.Reader) ([]byte, error) {
	client := &http.Client{}

	req, err := http.NewRequest("POST", url, body)
	if err != nil {
		return nil, err
	}

	req.Header.Set("key", key)

	req.Header.Set("Content-Type", "application/json")
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	resBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}
	res := &signalModel.GeneralRes{}
	err = json.Unmarshal(resBody, res)
	if err != nil {
		return nil, err
	}
	if res.Msg != "" {
		return nil, errors.New(res.Msg)
	}
	if res.Data == nil || res.Data.(string) == "" {
		return []byte{}, nil
	}
	return []byte(res.Data.(string)), nil
}

func SendingSDP(sdp webrtc.SessionDescription) error {
	route := ""
	payload, err := json.Marshal(sdp)
	if err != nil {
		return err
	}
	switch Now {
	case Offer:
		route = offerRoute
		req := signalModel.SdpPostReq{
			Data:   string(payload),
			KeyTTL: keyTTL,
		}
		payload, err = json.Marshal(req)
		if err != nil {
			return err
		}
	case Answer:
		route = answerRoute
	}

	uRL, err := url.JoinPath(Adder, route, "/sdp")
	if err != nil {
		return err
	}

	_, err = sendPostRequest(uRL, bytes.NewReader(payload))
	if err != nil {
		switch err.Error() {
		case signalCusterrors.SdpAlreadyExist:
			err = nil
			return err
		case signalCusterrors.KeyNotFound, signalCusterrors.KeyIsExpired:
			refreshKey()
			err = nil
			return err
		default:
			return err
		}
	}

	return nil
}

func GetSDP() (res webrtc.SessionDescription, err error) {
	route := ""
	switch Now {
	case Offer:
		route = offerRoute
	case Answer:
		route = answerRoute
	}

	uRL, err := url.JoinPath(Adder, route, "/sdp")
	if err != nil {
		return
	}

	result, err := sendGetRequest(uRL)
	if err != nil {
		switch err.Error() {
		case signalCusterrors.SdpNoValues,signalCusterrors.QueueGetFailBecauseNotExists:
			err = nil
			return
		case signalCusterrors.KeyNotFound, signalCusterrors.KeyIsExpired:
			refreshKey()
			err = nil
			return
		default:
			return
		}
	}
	err = json.Unmarshal(result, &res)
	if err != nil {
		return
	}
	return
}

func SendingCandidate(c *webrtc.ICECandidate) error {
	route := ""
	switch Now {
	case Offer:
		route = offerRoute
	case Answer:
		route = answerRoute
	}

	payload := []byte(c.ToJSON().Candidate)

	uRL, err := url.JoinPath(Adder, route, "/candidate")
	if err != nil {
		return err
	}

	_, err = sendPostRequest(uRL, bytes.NewReader(payload))
	if err != nil {
		switch err.Error() {
		case signalCusterrors.KeyNotFound, signalCusterrors.KeyIsExpired:
			refreshKey()
			err = nil
		default:
			return err
		}
	}
	return nil
}

func GetCandidate() (res []byte, err error) {
	route := ""
	switch Now {
	case Offer:
		route = offerRoute
	case Answer:
		route = answerRoute
	}

	uRL, err := url.JoinPath(Adder, route, "/candidate")
	if err != nil {
		return
	}
	res, err = sendGetRequest(uRL)
	if err != nil {
		switch err.Error() {
		case signalCusterrors.CandidateNoValues,signalCusterrors.QueueGetFailBecauseNotExists:
			err = nil
			return
		case signalCusterrors.KeyNotFound, signalCusterrors.KeyIsExpired:
			refreshKey()
			err = nil
			return
		default:
			return
		}
	}

	return
}
