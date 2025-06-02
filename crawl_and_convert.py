#!/usr/bin/env python3
"""
SEC-API 文档站点分析和转换工具
功能：
1. 分析 wget 下载的站点结构
2. 提取所有链接
3. 将 HTML 转换为 Markdown
4. 生成站点地图和分析报告
"""

import os
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from collections import defaultdict
from datetime import datetime

from bs4 import BeautifulSoup
from markitdown import MarkItDown
import html2text


class SiteAnalyzer:
    def __init__(self, download_dir, output_dir="output"):
        self.download_dir = Path(download_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # 初始化转换器
        self.markitdown = MarkItDown()
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = False
        self.html2text.ignore_images = False

        # 数据存储
        self.all_files = []
        self.all_links = defaultdict(list)
        self.internal_links = set()
        self.external_links = set()
        self.broken_links = []
        self.file_structure = {}

    def scan_files(self):
        """扫描所有 HTML 文件"""
        print("📁 扫描文件...")
        for file_path in self.download_dir.rglob("*.html"):
            self.all_files.append(file_path)

        print(f"✅ 找到 {len(self.all_files)} 个 HTML 文件")
        return self.all_files

    def extract_links(self):
        """从所有 HTML 文件中提取链接"""
        print("\n🔗 提取链接...")

        for file_path in self.all_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    soup = BeautifulSoup(f.read(), 'html.parser')

                # 提取页面标题
                title = soup.find('title')
                title_text = title.text.strip() if title else "无标题"

                # 获取相对路径
                relative_path = file_path.relative_to(self.download_dir)

                # 提取所有链接
                file_links = []
                for tag in soup.find_all(['a', 'link']):
                    href = tag.get('href')
                    if href:
                        file_links.append({
                            'href': href,
                            'text': tag.text.strip() if tag.name == 'a' else '',
                            'tag': tag.name
                        })

                        # 分类链接
                        if href.startswith(('http://', 'https://')):
                            if 'sec-api.io' in href:
                                self.internal_links.add(href)
                            else:
                                self.external_links.add(href)
                        elif href.startswith('/'):
                            self.internal_links.add(
                                f"https://sec-api.io{href}")

                self.all_links[str(relative_path)] = {
                    'title': title_text,
                    'links': file_links,
                    'path': str(file_path)
                }

            except Exception as e:
                print(f"❌ 处理文件失败 {file_path}: {e}")

        print(
            f"✅ 提取完成: {len(self.internal_links)} 个内部链接, {len(self.external_links)} 个外部链接")

    def check_broken_links(self):
        """检查死链接"""
        print("\n🔍 检查死链接...")

        for file_info in self.all_links.values():
            file_path = Path(file_info['path'])
            file_dir = file_path.parent

            for link_info in file_info['links']:
                href = link_info['href']

                # 只检查相对链接
                if not href.startswith(('http://', 'https://', '#', 'mailto:', 'javascript:')):
                    # 解析相对路径
                    if href.startswith('/'):
                        # 绝对路径
                        target_path = self.download_dir / \
                            'sec-api.io' / href.lstrip('/')
                    else:
                        # 相对路径
                        target_path = (file_dir / href).resolve()

                    # 检查文件是否存在
                    exists = (target_path.exists() or
                              target_path.with_suffix('.html').exists() or
                              (target_path / 'index.html').exists())

                    if not exists:
                        self.broken_links.append({
                            'source': str(file_path.relative_to(self.download_dir)),
                            'broken_link': href,
                            'expected_path': str(target_path.relative_to(self.download_dir))
                        })

        print(f"✅ 发现 {len(self.broken_links)} 个死链接")

    def convert_to_markdown(self):
        """将所有 HTML 文件转换为 Markdown"""
        print("\n📝 转换为 Markdown...")

        markdown_dir = self.output_dir / 'markdown'
        markdown_dir.mkdir(exist_ok=True)

        converted_count = 0
        failed_count = 0

        for file_path in self.all_files:
            try:
                # 读取 HTML
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()

                soup = BeautifulSoup(html_content, 'html.parser')

                # 获取标题
                title = soup.find('title')
                title_text = title.text.strip() if title else "Documentation"

                # 查找主要内容区域
                content = None
                for selector in ['main', 'article', '.content', '#content', '.docs-content']:
                    content = soup.select_one(selector)
                    if content:
                        break

                if not content:
                    content = soup.body if soup.body else soup

                # 尝试使用 markitdown
                try:
                    result = self.markitdown.convert(str(content))
                    markdown_content = result.text_content
                except:
                    # 降级使用 html2text
                    markdown_content = self.html2text.handle(str(content))

                # 构建输出路径
                relative_path = file_path.relative_to(self.download_dir)
                output_path = markdown_dir / relative_path.with_suffix('.md')
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # 写入 Markdown 文件
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(f"# {title_text}\n\n")
                    f.write(f"> 源文件: {relative_path}\n")
                    f.write(
                        f"> 转换时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("---\n\n")
                    f.write(markdown_content)

                converted_count += 1

            except Exception as e:
                print(f"❌ 转换失败 {file_path}: {e}")
                failed_count += 1

        print(f"✅ 转换完成: 成功 {converted_count} 个, 失败 {failed_count} 个")

    def generate_sitemap(self):
        """生成站点地图"""
        print("\n🗺️  生成站点地图...")

        sitemap = {
            'pages': [],
            'structure': {},
            'statistics': {}
        }

        # 构建页面列表
        for file_path in self.all_files:
            relative_path = file_path.relative_to(self.download_dir)

            # 转换为 URL
            url_parts = str(relative_path).replace('\\', '/').split('/')
            if url_parts[0] == 'sec-api.io':
                url_parts = url_parts[1:]

            url_path = '/'.join(url_parts)
            if url_path.endswith('/index.html'):
                url_path = url_path[:-11]
            elif url_path.endswith('.html'):
                url_path = url_path[:-5]

            # 获取页面信息
            file_key = str(relative_path)
            page_info = {
                'url': f"https://sec-api.io/{url_path}",
                'file': str(relative_path),
                'title': self.all_links.get(file_key, {}).get('title', ''),
                'links_count': len(self.all_links.get(file_key, {}).get('links', []))
            }

            sitemap['pages'].append(page_info)

            # 构建树形结构
            current = sitemap['structure']
            for part in url_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            file_name = url_parts[-1] if url_parts else 'index'
            current[file_name] = page_info['url']

        # 统计信息
        sitemap['statistics'] = {
            'total_pages': len(self.all_files),
            'total_internal_links': len(self.internal_links),
            'total_external_links': len(self.external_links),
            'broken_links': len(self.broken_links),
            'generated_at': datetime.now().isoformat()
        }

        # 保存站点地图
        with open(self.output_dir / 'sitemap.json', 'w', encoding='utf-8') as f:
            json.dump(sitemap, f, indent=2, ensure_ascii=False)

        print("✅ 站点地图已生成")

    def generate_report(self):
        """生成分析报告"""
        print("\n📊 生成分析报告...")

        report = []
        report.append("# SEC-API 文档站点分析报告\n")
        report.append(
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 基本统计
        report.append("## 📈 基本统计\n")
        report.append(f"- 总页面数: {len(self.all_files)}")
        report.append(f"- 内部链接: {len(self.internal_links)}")
        report.append(f"- 外部链接: {len(self.external_links)}")
        report.append(f"- 死链接: {len(self.broken_links)}\n")

        # 目录结构
        report.append("## 📁 目录结构\n")
        report.append("```")
        for file_path in sorted(self.all_files)[:20]:  # 只显示前20个
            relative_path = file_path.relative_to(self.download_dir)
            report.append(f"  {relative_path}")
        if len(self.all_files) > 20:
            report.append(f"  ... 还有 {len(self.all_files) - 20} 个文件")
        report.append("```\n")

        # 死链接报告
        if self.broken_links:
            report.append("## ❌ 死链接列表\n")
            for broken in self.broken_links[:10]:  # 只显示前10个
                report.append(f"- **{broken['source']}**")
                report.append(f"  - 链接: `{broken['broken_link']}`")
                report.append(f"  - 期望路径: `{broken['expected_path']}`\n")

            if len(self.broken_links) > 10:
                report.append(f"... 还有 {len(self.broken_links) - 10} 个死链接\n")

        # 外部链接
        report.append("## 🌐 外部链接域名统计\n")
        external_domains = defaultdict(int)
        for link in self.external_links:
            domain = urlparse(link).netloc
            external_domains[domain] += 1

        for domain, count in sorted(external_domains.items(), key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"- {domain}: {count} 个链接")

        # 保存报告
        report_path = self.output_dir / 'analysis_report.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report))

        print("✅ 报告已生成")

        # 同时保存详细的 JSON 数据
        detailed_data = {
            'all_links': dict(self.all_links),
            'internal_links': list(self.internal_links),
            'external_links': list(self.external_links),
            'broken_links': self.broken_links,
            'file_list': [str(f.relative_to(self.download_dir)) for f in self.all_files]
        }

        with open(self.output_dir / 'detailed_analysis.json', 'w', encoding='utf-8') as f:
            json.dump(detailed_data, f, indent=2, ensure_ascii=False)

    def run(self):
        """运行完整的分析流程"""
        print("🚀 开始分析 SEC-API 文档站点\n")

        # 1. 扫描文件
        self.scan_files()

        # 2. 提取链接
        self.extract_links()

        # 3. 检查死链接
        self.check_broken_links()

        # 4. 转换为 Markdown
        self.convert_to_markdown()

        # 5. 生成站点地图
        self.generate_sitemap()

        # 6. 生成报告
        self.generate_report()

        print("\n✨ 分析完成！")
        print(f"📂 输出目录: {self.output_dir.absolute()}")
        print("📄 文件列表:")
        print(f"  - markdown/: 转换后的 Markdown 文件")
        print(f"  - sitemap.json: 站点地图")
        print(f"  - analysis_report.md: 分析报告")
        print(f"  - detailed_analysis.json: 详细数据")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='分析 wget 下载的站点并转换为 Markdown')
    parser.add_argument('download_dir', help='wget 下载的目录路径')
    parser.add_argument('-o', '--output', default='output',
                        help='输出目录 (默认: output)')

    args = parser.parse_args()

    # 检查下载目录是否存在
    if not os.path.exists(args.download_dir):
        print(f"❌ 错误: 目录 '{args.download_dir}' 不存在")
        print("\n请先使用 wget 下载站点:")
        print("wget --mirror --convert-links --page-requisites --no-parent \\")
        print("     --directory-prefix=sec-api-docs \\")
        print("     https://sec-api.io/docs")
        return

    # 运行分析
    analyzer = SiteAnalyzer(args.download_dir, args.output)
    analyzer.run()


if __name__ == "__main__":
    main()
