#!/usr/bin/python
# -*- coding: UTF-8 -*-
import sys
import os
import time
import requests
import json
import configparser
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# 禁用 SSL 警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 检查 Python 版本
version = sys.version_info
if version < (3, 0):
    print('当前版本不支持，请使用 Python 3')
    sys.exit()

# 初始化全局变量
add_count_suss = 0
error_count = 0

# 读取配置文件
print('初始化中...')
cf = configparser.ConfigParser()
try:
    cf.read("config.ini", encoding='utf-8')
    awvs_url = cf.get('awvs_url_key', 'awvs_url')
    api_key = cf.get('awvs_url_key', 'api_key')
    domain_file = cf.get('awvs_url_key', 'domain_file')
    scan_speed = cf.get('scan_seting', 'scan_speed').strip()
except Exception as e:
    print(f'初始化失败，请检查 config.ini 文件配置是否正确\n{e}')
    sys.exit()

# 设置请求头
headers = {'Content-Type': 'application/json', "X-Auth": api_key}

# 创建日志目录
if not os.path.exists('./add_log'):
    os.makedirs('./add_log')

# 添加目标函数（批量添加）
def add_targets_batch(targets):
    global add_count_suss, error_count, awvs_url
    url = f"{awvs_url}/api/v1/targets/add"
    formatted_targets = []
    
    # 格式化目标列表
    for target in targets:
        target = target.strip()
        if target and 'http' not in target[0:7]:
            target = 'http://' + target
        formatted_targets.append({"address": target, "description": "批量添加任务"})
    
    if not formatted_targets:
        return

    try:
        data = {"targets": formatted_targets, "groups": []}
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10, verify=False)
        result = json.loads(response.content.decode())
        
        # 处理返回结果
        for i, target in enumerate(result['targets']):
            target_address = formatted_targets[i]['address']
            try:
                target_id = target['target_id']
                with open('./add_log/success.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{target_address}\n")
                add_count_suss += 1
                print(f"{target_address} 已加入到扫描队列，第: {add_count_suss}")
            except KeyError:
                with open('./add_log/error_url.txt', 'a', encoding='utf-8') as f:
                    f.write(f"{target_address}\n")
                error_count += 1
                print(f"{target_address} 添加失败，第: {error_count}")
    except Exception as e:
        for target in formatted_targets:
            with open('./add_log/error_url.txt', 'a', encoding='utf-8') as f:
                f.write(f"{target['address']}\n")
            error_count += 1
            print(f"{target['address']} 添加失败，错误: {e}")

# 主函数
def main():
    global domain_file
    
    # 读取目标 URL 文件
    try:
        with open(domain_file, 'r', encoding='utf-8') as f:
            targets = [line.strip() for line in f.readlines() if line.strip()]
    except Exception as e:
        print(f"无法读取 {domain_file} 文件，请检查文件是否存在或路径是否正确\n{e}")
        sys.exit()

    if not targets:
        print("目标列表为空，请检查 url.txt 文件内容")
        sys.exit()

    print(f"开始批量添加 {len(targets)} 个目标...")

    # 分批处理，每批 50 个目标
    batch_size = 50
    for i in range(0, len(targets), batch_size):
        batch = targets[i:i + batch_size]
        print(f"正在处理第 {i // batch_size + 1} 批，共 {len(batch)} 个目标...")
        add_targets_batch(batch)
        time.sleep(2)  # 添加短暂延迟，避免请求过快被限制

    print(f"\n添加完成！成功: {add_count_suss} 个，失败: {error_count} 个")

if __name__ == '__main__':
    print("""
********************************************************************      
AWVS 批量添加任务脚本（单线程，批量添加）                                                                                                      
作者微信：SRC-ALL
当前日期：{}
********************************************************************
""".format(time.strftime("%Y-%m-%d %H:%M:%S")))
    main()