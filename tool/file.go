//Copyright (c) [2023] [JinCanQi]
//[make_data_set_so-vits-svc] is licensed under Mulan PubL v2.
//You can use this software according to the terms and conditions of the Mulan PubL v2.
//You may obtain a copy of Mulan PubL v2 at:
//         http://license.coscl.org.cn/MulanPubL-2.0
//THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
//EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
//MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
//See the Mulan PubL v2 for more details.

package tool

import (
	"errors"
	"fmt"
	"io"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"strings"
)

func FuzzySearchFiles(dir string, nameList []string) (result []string, err error) {
	err = filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		for _, v := range nameList {
			if strings.Contains(info.Name(), v) {
				result = append(result, path)
			}
		}
		return nil
	})
	if err != nil {
		return
	}
	return
}

//这是一个 Go 语言的函数，它接受三个字符串参数 aDir、bDir 和 cDir。
//它调用 GetFolderAllFiles 函数来获取 aDir 和 bDir 目录中的所有文件。
//然后它循环遍历 aDir 和 bDir 中的每个文件，并检查 aDir 中文件的基本名称是否与 bDir 中文件的基本名称相同。
//如果它们相同，它调用 Copy 函数将文件从 aDir 复制到 cDir，并使用相同的名称。
//如果任何操作失败，该函数将返回一个错误。
func PlaceFilesWithTheSameNameAsFolderAAndFolderBInFolderC(aDir, bDir, cDir string) (err error) {
	aFiles, err := GetFolderAllFiles(aDir)
	if err != nil {
		return
	}
	bFiles, err := GetFolderAllFiles(bDir)
	if err != nil {
		return
	}
	for _, aFile := range aFiles {
		for _, bFile := range bFiles {
			if RecoverUltimatevocalremoverFileName(filepath.Base(aFile)) == filepath.Base(bFile) {
				_, err = Copy(aFile, filepath.Join(cDir, RecoverUltimatevocalremoverFileName(filepath.Base(aFile))))
				if err != nil {
					return
				}
			}
		}
	}
	return
}

func GetFolderAllFiles(dir string) (files []string, err error) {
	err = filepath.WalkDir(dir, func(path string, info fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() {
			files = append(files, path)
		} else {
			if path != dir {
				return filepath.SkipDir
			}
		}
		return nil
	})
	if err != nil {
		return
	}
	return
}

func Copy(src, dst string) (int64, error) {
	srcFile, err := os.Open(src)
	if err != nil {
		return 0, err
	}
	defer srcFile.Close()
	// 判断存在
	_, err = os.Stat(dst)
	if err == nil || errors.Is(err, os.ErrExist) {
		if err == nil {
			log.Printf("%s 已经存在\n", dst)
		} else if errors.Is(err, os.ErrExist) {
			log.Printf("%s 已经存在，且因某种原因可能是权限导致无法读取\n", dst)
		}

		// /path/to/parent_directory/filename_copy.ext
		dst = fmt.Sprintf("%s_copy%s", strings.TrimSuffix(dst, filepath.Ext(dst)), filepath.Ext(dst))
		log.Printf("尝试将文件复制到 %s\n", dst)
	}

	dstFile, err := os.Create(dst)
	if err != nil {
		return 0, err
	}
	defer dstFile.Close()
	return io.Copy(dstFile, srcFile)
}

func RecoverUltimatevocalremoverFileName(fileName string) (result string) {
	// 将文件名 1_1-13-2023-04-18-再见拜拜_(Vocals).mp3 改为 1-13-2023-04-18-再见拜拜.mp3
	// 将文件名 4_4-13-2023-01-17-独处_(Instrumental).mp3 改为 4-13-2023-01-17-独处.mp3
	//查找第一个下划线
	firstIndex := strings.Index(fileName, "_")
	//查找最后一个下划线
	lastIndex := strings.LastIndex(fileName, "_")
	return fmt.Sprint(fileName[firstIndex+1:lastIndex], filepath.Ext(fileName))
}
