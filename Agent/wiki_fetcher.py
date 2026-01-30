"""
维基页面抓取工具 - 用于从饥荒维基获取页面源代码以供 AI 参考

使用场景：
1. 需要了解特定模板的用法（如信息框、导航框等）
2. 需要参考高质量页面的编写风格
3. 需要查看特定实体的维基数据结构
4. 不确定某个术语或概念的维基表述方式

使用方法：
1. 直接运行：抓取默认页面列表
   python Agent/wiki_fetcher.py

2. 指定页面：抓取特定页面
   python Agent/wiki_fetcher.py "寄居蟹隐士" "拆解魔杖"

3. 按模板抓取：抓取使用特定模板的页面
   python Agent/wiki_fetcher.py --template "角色信息框" --limit 5

4. 按分类抓取：抓取特定分类的页面
   python Agent/wiki_fetcher.py --category "联机版" --limit 10
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import *
import argparse
from datetime import datetime


# 默认抓取的页面列表（高质量示例页面）
DEFAULT_PAGES = [
    # 编写规范
    "帮助:编写规范",
    "帮助:译名表",

    # 高质量角色页面示例
    "薇克巴顿",
    "温蒂",

    # 高质量物品页面示例
    "拆解魔杖",
    "建造护符",

    # 高质量生物/NPC页面示例
    "寄居蟹隐士",
    "蜘蛛战士",

    # 模板使用示例
    "模板:实体信息框/自动",
    "模板:角色信息框",
    "模板:Pic",
]


def fetch_pages(page_names, output_file="Agent/fetched_content.json"):
    """抓取指定页面的源代码"""
    fetched_content = {}
    failed_pages = []

    print(f"开始抓取 {len(page_names)} 个页面...")

    for page_name in tqdm(page_names):
        try:
            page = site.pages[page_name]
            if not page.exists:
                print(f"⚠ 页面不存在: {page_name}")
                failed_pages.append(page_name)
                continue

            content = page.text()
            # 保存页面元数据
            fetched_content[page_name] = {
                "content": content,
                "length": len(content),
                "fetched_at": datetime.now().isoformat(),
                "url": f"https://dontstarve.huijiwiki.com/wiki/{page_name.replace(' ', '_')}"
            }
        except Exception as e:
            print(f"✗ 无法抓取 {page_name}: {e}")
            failed_pages.append(page_name)

    # 保存抓取结果
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(fetched_content, f, ensure_ascii=False, indent=2)

    # 输出统计信息
    print(f"\n✓ 成功抓取 {len(fetched_content)} 个页面")
    print(f"✓ 保存到: {output_file}")
    print("\n页面统计:")
    for name, data in fetched_content.items():
        print(f"  - {name}: {data['length']} 字符")

    if failed_pages:
        print(f"\n✗ 失败 {len(failed_pages)} 个页面:")
        for name in failed_pages:
            print(f"  - {name}")

    return fetched_content


def fetch_by_template(template_name, limit=10):
    """抓取使用特定模板的页面"""
    print(f"查找使用模板 '{template_name}' 的页面...")
    pages = get_pages(template=template_name)

    if not pages:
        print(f"未找到使用模板 '{template_name}' 的页面")
        return []

    page_names = [p.name for p in pages[:limit]]
    print(f"找到 {len(pages)} 个页面，抓取前 {len(page_names)} 个")
    return page_names


def fetch_by_category(category_name, limit=10):
    """抓取特定分类的页面"""
    print(f"查找分类 '{category_name}' 下的页面...")
    pages = get_pages(category=category_name)

    if not pages:
        print(f"未找到分类 '{category_name}' 下的页面")
        return []

    page_names = [p.name for p in pages[:limit]]
    print(f"找到 {len(pages)} 个页面，抓取前 {len(page_names)} 个")
    return page_names


def load_fetched_content(input_file="Agent/fetched_content.json"):
    """加载已抓取的内容"""
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def search_in_fetched(keyword, input_file="Agent/fetched_content.json"):
    """在已抓取的内容中搜索关键词"""
    content = load_fetched_content(input_file)
    results = []

    for page_name, data in content.items():
        if keyword.lower() in data["content"].lower():
            results.append(page_name)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="从饥荒维基抓取页面源代码",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "pages",
        nargs="*",
        help="要抓取的页面名称列表"
    )

    parser.add_argument(
        "-t", "--template",
        help="抓取使用指定模板的页面"
    )

    parser.add_argument(
        "-c", "--category",
        help="抓取指定分类下的页面"
    )

    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=10,
        help="抓取数量限制（默认：10）"
    )

    parser.add_argument(
        "-o", "--output",
        default="Agent/fetched_content.json",
        help="输出文件路径（默认：Agent/fetched_content.json）"
    )

    parser.add_argument(
        "-s", "--search",
        help="在已抓取的内容中搜索关键词"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="列出已抓取的页面"
    )

    args = parser.parse_args()

    # 列出已抓取的页面
    if args.list:
        content = load_fetched_content(args.output)
        if not content:
            print("还没有抓取任何页面")
            return

        print(f"已抓取 {len(content)} 个页面:")
        for name, data in content.items():
            print(f"  - {name}")
            print(f"    长度: {data['length']} 字符")
            print(f"    抓取时间: {data['fetched_at']}")
            print(f"    URL: {data['url']}")
        return

    # 搜索关键词
    if args.search:
        results = search_in_fetched(args.search, args.output)
        if results:
            print(f"在 {len(results)} 个页面中找到关键词 '{args.search}':")
            for page_name in results:
                print(f"  - {page_name}")
        else:
            print(f"未找到包含关键词 '{args.search}' 的页面")
        return

    # 确定要抓取的页面列表
    page_names = []

    if args.pages:
        # 使用命令行参数指定的页面
        page_names = args.pages
    elif args.template:
        # 按模板抓取
        page_names = fetch_by_template(args.template, args.limit)
    elif args.category:
        # 按分类抓取
        page_names = fetch_by_category(args.category, args.limit)
    else:
        # 使用默认页面列表
        page_names = DEFAULT_PAGES
        print("使用默认页面列表（高质量示例页面）")

    if not page_names:
        print("没有要抓取的页面")
        return

    # 执行抓取
    fetch_pages(page_names, args.output)


if __name__ == "__main__":
    main()
