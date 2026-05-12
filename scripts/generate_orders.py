import os
import csv
import random
from datetime import date, timedelta

# ========================
# 全局配置
# ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TODAY = date(2026, 5, 12)
DATES = [TODAY - timedelta(days=i) for i in range(1, 4)]
DATE_MIN, DATE_MAX = DATES[-1], DATES[0]

SKU_POOL = {
    "SKU1001": ((25.0, 35.0), (10.0, 15.0), (2.0, 5.0)),
    "SKU1002": ((15.0, 20.0), (8.0, 10.0), (2.0, 4.0)),
    "SKU1003": ((40.0, 60.0), (20.0, 30.0), (5.0, 8.0)),
    "SKU1004": ((10.0, 12.0), (5.0, 7.0), (1.0, 3.0)),
}

PLATFORM_CONFIG = {
    "amazon": {
        "count": (12, 16),
        "sku_probs": {"SKU1001": 0.7, "SKU1002": 0.2, "SKU1003": 0.1},
        "loss_rate": 0.2,
    },
    "tiktok": {
        "count": (10, 14),
        "sku_probs": {"SKU1001": 0.5, "SKU1002": 0.3, "SKU1003": 0.15, "SKU1004": 0.05},
        "loss_rate": 0.3,
    },
    "1688": {
        "count": (10, 15),
        "sku_probs": {"SKU1001": 0.4, "SKU1002": 0.3, "SKU1003": 0.2, "SKU1004": 0.1},
        "loss_rate": 0.25,
    },
}

def weighted_choice(prob_map):
    r = random.random()
    cumulative = 0.0
    for key, prob in prob_map.items():
        cumulative += prob
        if r < cumulative:
            return key
    return list(prob_map.keys())[-1]

def random_range(rng):
    return round(random.uniform(rng[0], rng[1]), 2)

def generate_order(platform, order_index, sku, is_loss, date_str):
    sale_range, cost_range, ship_range = SKU_POOL[sku]
    cost = random_range(cost_range)
    shipping = random_range(ship_range)

    if is_loss:
        sale_price = round(random.uniform(0.0, cost + shipping - 0.01), 2)
        if sale_price < 0:
            sale_price = 0.01
    else:
        floor = cost + shipping + 2.0
        sale_price = round(random.uniform(floor, floor + random_range((5, 15))), 2)

    quantity = random.randint(1, 3)

    if platform == "amazon":
        order_id = f"AMZN_{order_index:04d}"
    elif platform == "tiktok":
        order_id = f"TK_{order_index:04d}"
    else:
        order_id = f"1688_{order_index:04d}"

    return {
        "order_id": order_id,
        "platform": platform,
        "sku": sku,
        "sale_price": f"{sale_price:.2f}",
        "cost_price": f"{cost:.2f}",
        "shipping_fee": f"{shipping:.2f}",
        "order_date": date_str,
        "quantity": str(quantity),
    }

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    all_platform_data = {}
    global_order_counter = 1

    for platform, config in PLATFORM_CONFIG.items():
        min_count, max_count = config["count"]
        num_orders = random.randint(min_count, max_count)

        forced_date11 = 3
        orders_for_platform = []

        date_pool = []
        date_pool.extend([str(DATE_MAX)] * forced_date11)
        for _ in range(num_orders - forced_date11):
            d = random.choice(DATES)
            date_pool.append(str(d))
        random.shuffle(date_pool)

        for i in range(num_orders):
            sku = weighted_choice(config["sku_probs"])
            is_loss = random.random() < config["loss_rate"]
            order = generate_order(
                platform,
                global_order_counter,
                sku,
                is_loss,
                date_pool[i],
            )
            orders_for_platform.append(order)
            global_order_counter += 1

        filepath = os.path.join(DATA_DIR, f"{platform}.csv")
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "order_id", "platform", "sku", "sale_price",
                "cost_price", "shipping_fee", "order_date", "quantity"
            ])
            writer.writeheader()
            writer.writerows(orders_for_platform)

        all_platform_data[platform] = orders_for_platform
        print(f"✅ {platform}.csv 生成完毕，共 {len(orders_for_platform)} 条数据")

    # 自校验
    print("\n🔍 开始自校验...")
    total_loss = 0
    unique_skus = set()
    date_11_count = 0

    for platform, orders in all_platform_data.items():
        for o in orders:
            sale = float(o["sale_price"])
            cost = float(o["cost_price"])
            ship = float(o["shipping_fee"])
            if sale < cost + ship:
                total_loss += 1
            unique_skus.add(o["sku"])
            if o["order_date"] == "2026-05-11":
                date_11_count += 1

    print(f"  不重复 SKU 数量：{len(unique_skus)} (要求 >=3)")
    print(f"  亏损订单总数：{total_loss} (要求 >=2)")
    print(f"  2026-05-11 订单数：{date_11_count} (要求 >=3)")

    if len(unique_skus) >= 3 and total_loss >= 2 and date_11_count >= 3:
        print("🎉 所有校验通过，数据生成成功！")
    else:
        print("❌ 校验未完全通过，请检查生成逻辑。")

    print("\n📋 文件预览（前3行）：")
    for platform in ["amazon", "tiktok", "1688"]:
        filepath = os.path.join(DATA_DIR, f"{platform}.csv")
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            print(f"\n--- {platform}.csv ---")
            for line in lines[:4]:
                print(line.strip())

if __name__ == "__main__":
    random.seed(42)
    main()
