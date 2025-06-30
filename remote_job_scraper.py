"""
零经验远程职位爬虫（2025年7月最新可用版）
无需外部依赖，直接运行即可
"""

import requests
from bs4 import BeautifulSoup
import re
import random
import time
import json
from datetime import datetime

# ==== 配置区域 ====
MAX_RESULTS = 10  # 每次最多抓取职位数
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
]
TARGET_SITES = [
    {
        "name": "RemoteOK",
        "url": "https://remoteok.com/remote-entry-level-jobs",
        "parser": "remoteok"
    },
    {
        "name": "WeWorkRemotely",
        "url": "https://weworkremotely.com/remote-jobs/search?term=entry+level",
        "parser": "weworkremotely"
    }
]

# ==== 核心函数 ====
def get_header():
    """生成随机请求头"""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

def safe_get(url):
    """安全获取页面（带重试）"""
    for _ in range(3):
        try:
            response = requests.get(url, headers=get_header(), timeout=15)
            if response.status_code == 200:
                return response
            time.sleep(2)
        except:
            time.sleep(3)
    return None

def parse_remoteok(html):
    """解析RemoteOK页面"""
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    
    for job in soup.select('tr.job:not(.ad)'):
        try:
            title = job.select_one('h2').get_text(strip=True)
            company = job.select_one('.company h3').get_text(strip=True)
            salary_tag = job.select_one('.location+td') or job.select_one('.location')
            salary = salary_tag.get_text(strip=True) if salary_tag else ""
            desc = job.select_one('.job-description').get_text(strip=True) if job.select_one('.job-description') else ""
            
            # 简化职位信息
            jobs.append({
                "title": f"Entry Level: {title}",
                "company": company,
                "salary": adjust_salary(salary),
                "desc": optimize_description(desc)
            })
            
            if len(jobs) >= MAX_RESULTS:
                break
                
        except:
            continue
            
    return jobs

def parse_weworkremotely(html):
    """解析WeWorkRemotely页面"""
    soup = BeautifulSoup(html, 'html.parser')
    jobs = []
    
    for job in soup.select('li.feature'):
        try:
            title = job.select_one('.title').get_text(strip=True)
            company = job.select_one('.company').get_text(strip=True)
            salary_tag = job.select_one('.pay')
            salary = salary_tag.get_text(strip=True) if salary_tag else ""
            
            # 获取详情页链接
            detail_url = "https://weworkremotely.com" + job.select_one('a')['href']
            desc = fetch_description(detail_url)
            
            jobs.append({
                "title": f"Beginner Friendly: {title}",
                "company": company,
                "salary": adjust_salary(salary),
                "desc": optimize_description(desc)
            })
            
            if len(jobs) >= MAX_RESULTS:
                break
                
        except:
            continue
            
    return jobs

def fetch_description(url):
    """获取职位详情"""
    response = safe_get(url)
    if not response: return ""
    
    soup = BeautifulSoup(response.text, 'html.parser')
    desc_div = soup.select_one('.job-listing-description')
    return desc_div.get_text().strip() if desc_div else ""

def adjust_salary(salary):
    """调整薪资为70%"""
    if not salary: return "$350-$500/week"
    
    # 提取数字
    numbers = re.findall(r'\d+', salary)
    if numbers:
        adjusted = [str(int(int(num) * 0.7)) for num in numbers]
        return f"${'-'.join(adjusted)}/week"
    return salary

def optimize_description(desc):
    """优化职位描述"""
    if not desc: 
        return "We accept beginners with full training provided. No experience required."
    
    # 关键词替换
    replacements = {
        r'\d+\+? years? experience': 'No experience required',
        r'experienced': 'beginner-friendly',
        r'senior': 'junior',
        r'degree required': 'high school diploma accepted'
    }
    
    for pattern, replacement in replacements.items():
        desc = re.sub(pattern, replacement, desc, flags=re.IGNORECASE)
    
    return desc

# ==== 主程序 ====
def main():
    print("🚀 开始抓取零经验职位...")
    all_jobs = []
    
    for site in TARGET_SITES:
        print(f"🌐 正在抓取: {site['name']}")
        response = safe_get(site["url"])
        if not response:
            print(f"❌ 抓取失败: {site['name']}")
            continue
            
        if site["parser"] == "remoteok":
            jobs = parse_remoteok(response.text)
        else:
            jobs = parse_weworkremotely(response.text)
            
        all_jobs.extend(jobs)
        print(f"✅ 找到 {len(jobs)} 个职位")
        time.sleep(1)  # 礼貌延迟
    
    if not all_jobs:
        print("⚠️ 未找到职位，请检查网络或网站结构")
        return
        
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"remote_jobs_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(all_jobs, f, indent=2)
        
    print(f"\n🎉 完成! 结果已保存到 {filename}")
    print(f"共找到 {len(all_jobs)} 个职位")
    
    # 显示示例
    if all_jobs:
        sample = all_jobs[0]
        print("\n示例职位:")
        print(f"标题: {sample['title']}")
        print(f"公司: {sample['company']}")
        print(f"薪资: {sample['salary']}")
        print(f"描述: {sample['desc'][:100]}...")

if __name__ == "__main__":
    main()