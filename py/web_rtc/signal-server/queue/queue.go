//Copyright (c) [2023] [JinCanQi]
//[make_data_set_so-vits-svc] is licensed under Mulan PubL v2.
//You can use this software according to the terms and conditions of the Mulan PubL v2.
//You may obtain a copy of Mulan PubL v2 at:
//         http://license.coscl.org.cn/MulanPubL-2.0
//THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
//EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
//MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
//See the Mulan PubL v2 for more details.

package queue

import (
	"fmt"
	"log"
	"make_data_set_so-vits-svc/py/web_rtc/signal-server/custerrors"
	"sync"

	"github.com/gogf/gf/v2/container/gqueue"
)

var (
	queueMap = &sync.Map{}
)

const (
	offerSdpKey        = "offer_sdp_%s"
	offerCandidateKey  = "offer_candidate_%s"
	answerSdpKey       = "answer_sdp_%s"
	answerCandidateKey = "answer_candidate_%s"
)

type MyQueue interface {
	Close()
	Push(v interface{})
	Pop() interface{}
	Len() (length int64)
	Size() int64

	GetMyQueue() *myQueue
}

type myQueue struct {
	*gqueue.Queue
	Key string
}

func NewOfferSdpQueue(key string) MyQueue {
	varMyQueue := &myQueue{Key: fmt.Sprintf(offerSdpKey, key)}

	if _, ok := queueMap.Load(varMyQueue.Key); ok {
		log.Panicln(custerrors.QueueNewFailBecauseAlreadyExists)
	}

	queue := gqueue.New()
	queueMap.Store(varMyQueue.Key, queue)
	varMyQueue.Queue = queue
	return varMyQueue
}
func GetOfferSdpQueue(key string) MyQueue {
	varMyQueue := &myQueue{Key: fmt.Sprintf(offerSdpKey, key)}

	if queue, ok := queueMap.Load(varMyQueue.Key); ok {
		varMyQueue.Queue = queue.(*gqueue.Queue)
		return varMyQueue
	}
	log.Panicln(custerrors.QueueGetFailBecauseNotExists)
	return nil
}

func NewOfferCandidateQueue(key string) MyQueue {
	varMyQueue := &myQueue{Key: fmt.Sprintf(offerCandidateKey, key)}

	if _, ok := queueMap.Load(varMyQueue.Key); ok {
		log.Panicln(custerrors.QueueNewFailBecauseAlreadyExists)
	}

	queue := gqueue.New()
	queueMap.Store(varMyQueue.Key, queue)
	varMyQueue.Queue = queue
	return varMyQueue
}
func GetOfferCandidateQueue(key string) MyQueue {
	varMyQueue := &myQueue{Key: fmt.Sprintf(offerCandidateKey, key)}

	if queue, ok := queueMap.Load(varMyQueue.Key); ok {
		varMyQueue.Queue = queue.(*gqueue.Queue)
		return varMyQueue
	}
	log.Panicln(custerrors.QueueGetFailBecauseNotExists)
	return nil
}

func NewAnswerSdpQueue(key string) MyQueue {
	varMyQueue := &myQueue{Key: fmt.Sprintf(answerSdpKey, key)}

	if _, ok := queueMap.Load(varMyQueue.Key); ok {
		log.Panicln(custerrors.QueueNewFailBecauseAlreadyExists)
	}

	queue := gqueue.New()
	queueMap.Store(varMyQueue.Key, queue)
	varMyQueue.Queue = queue
	return varMyQueue
}
func GetAnswerSdpQueue(key string) MyQueue {
	varMyQueue := &myQueue{Key: fmt.Sprintf(answerSdpKey, key)}

	if queue, ok := queueMap.Load(varMyQueue.Key); ok {
		varMyQueue.Queue = queue.(*gqueue.Queue)
		return varMyQueue
	}
	log.Panicln(custerrors.QueueGetFailBecauseNotExists)
	return nil
}

func NewAnswerCandidateQueue(key string) MyQueue {
	varMyQueue := &myQueue{Key: fmt.Sprintf(answerCandidateKey, key)}

	if _, ok := queueMap.Load(varMyQueue.Key); ok {
		log.Panicln(custerrors.QueueNewFailBecauseAlreadyExists)
	}

	queue := gqueue.New()
	queueMap.Store(varMyQueue.Key, queue)
	varMyQueue.Queue = queue
	return varMyQueue
}
func GetAnswerCandidateQueue(key string) MyQueue {
	varMyQueue := &myQueue{Key: fmt.Sprintf(answerCandidateKey, key)}

	if queue, ok := queueMap.Load(varMyQueue.Key); ok {
		varMyQueue.Queue = queue.(*gqueue.Queue)
		return varMyQueue
	}
	log.Panicln(custerrors.QueueGetFailBecauseNotExists)
	return nil
}

// Close Close由cache的OnEvict触发，调用此方法会关闭此队列，通常只有在请求方已经与对方建立webrtc连接后（信令服务器已完成服务）才会调用此方法
func (m *myQueue) Close() {
	m.Queue.Close()
	queueMap.Delete(m.Key)
}

func (m *myQueue) GetMyQueue() *myQueue {
	return m
}
