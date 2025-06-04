import asyncio
import pandas as pd
from pydoll.browser.chrome import Chrome
from pydoll.constants import By
import time

# List of coins to scrape
list_coin = [
    'bitcoin', 'ethereum', 'binance', 'solana'
]

async def get_element_text(page, element):
    """Helper function to get text from element using CDP commands"""
    try:
        if element and hasattr(element, '_object_id'):
            # Sử dụng Runtime.callFunctionOn để lấy text content
            command = {
                "id": 1,
                "method": "Runtime.callFunctionOn",
                "params": {
                    "functionDeclaration": "function() { return this.textContent || this.innerText || ''; }",
                    "objectId": element._object_id,
                    "returnByValue": True
                }
            }
            
            result = await page._connection_handler.execute_command(command)
            
            if result and 'result' in result and 'result' in result['result'] and 'value' in result['result']['result']:
                text = result['result']['result']['value'].strip()
                return text if text else "N/A"
            else:
                return "N/A"
        else:
            return "N/A"
    except Exception as e:
        print(f"⚠️ Error getting text from element: {e}")
        # Fallback: Thử dùng JavaScript evaluation trên page
        try:
            if element and hasattr(element, '_object_id'):
                # Fallback method: dùng Runtime.getProperties
                return "N/A"  # Simplified fallback
            else:
                return "N/A"
        except:
            return "N/A"

async def fetch_coin_data(coin):
    url = f'https://www.bitget.com/price/{coin}'
    print(f"🔎 Starting crawl: {coin}")

    browser = Chrome()
    
    try:
        await browser.start()
        page = await browser.get_page()
        
        await page.go_to(url)
        print(f"📄 Page loaded: {coin}")
        
        await asyncio.sleep(3)

        try:
            # Dùng XPath chính xác như Selenium
            price_elem = await page.wait_element(
                By.XPATH, 
                '//span[@class="font-bold text-[40px] ltIpad:text-[32px] leading-[48px] ltIpad:leading-[38px] text-primaryText"]',
                timeout=10
            )
            price = await get_element_text(page, price_elem) if price_elem else "N/A"

            # Dùng XPath chính xác cho date
            try:
                date_elem = await page.wait_element(
                    By.XPATH, 
                    '//div[@class="text-[14px] mt-[24px] text-thirdText font-medium"]',
                    timeout=5
                )
                date = await get_element_text(page, date_elem) if date_elem else "N/A"
            except Exception:
                date = "N/A"

            data = {'coin': coin, 'price': price, 'date': date}
            
            try:
                # Dùng XPath chính xác như Selenium
                labels = await page.find_elements(
                    By.XPATH, 
                    '//span[@class="text-[14px] text-[var(--content-secondary)]"]'
                )
                values = await page.find_elements(
                    By.XPATH, 
                    '//span[@class="text-[14px] font-[600]"]'
                )

                if labels and values:
                    keys = [await get_element_text(page, el) for el in labels[:5]]
                    vals = [await get_element_text(page, el) for el in values[:5]]
                    
                    limit = min(len(keys), len(vals))
                    for i in range(limit):
                        if keys[i] and vals[i] and keys[i] != "N/A" and vals[i] != "N/A":
                            clean_key = keys[i].strip(':').strip()
                            clean_val = vals[i].strip()
                            if clean_key and clean_val:
                                data[clean_key] = clean_val

            except Exception as e:
                print(f"⚠️ Unable to fetch additional info for {coin}: {e}")

            print(f"✅ Crawl completed: {coin}")
            return data

        except Exception as e:
            print(f"❌ Error finding element for {coin}: {e}")
            return {'coin': coin, 'error': str(e)}

    except Exception as e:
        print(f"❌ Error crawling {coin}: {e}")
        return {'coin': coin, 'error': str(e)}

    finally:
        try:
            await browser.stop()
        except Exception as e:
            print(f"⚠️ Error closing browser for {coin}: {e}")

async def crawl_single_coin(coin):
    """Crawl a single coin with retry logic"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            result = await fetch_coin_data(coin)
            if 'error' not in result:
                return result
            else:
                print(f"🔄 Retrying {coin} attempt {attempt + 1}")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"🔄 Error attempt {attempt + 1} for {coin}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
    
    return {'coin': coin, 'error': 'Failed after retries'}

async def main():
    print("🚀 Starting cryptocurrency data crawling...")
    print("Debug: Starting main function")
    
    print(f"🧪 Testing with all coins concurrently...")
    print("Debug: About to start concurrent crawl")
    
    try:
        # Tạo tasks cho tất cả coins cùng lúc
        tasks = []
        for coin in list_coin:
            task = asyncio.create_task(crawl_single_coin(coin))
            tasks.append(task)
            print(f"📋 Created task for {coin}")
        
        print(f"🚀 Starting {len(tasks)} concurrent crawl tasks...")
        
        # Chạy tất cả tasks đồng thời và chờ kết quả
        all_data = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Xử lý kết quả và exceptions
        processed_data = []
        for i, result in enumerate(all_data):
            coin = list_coin[i]
            if isinstance(result, Exception):
                print(f"❌ Exception for {coin}: {result}")
                processed_data.append({'coin': coin, 'error': str(result)})
            else:
                processed_data.append(result)
        
        print(f"📋 All crawl tasks completed")

        try:
            df = pd.DataFrame(processed_data)
            excel_file = "bitget_coin_data.xlsx"
            df.to_excel(excel_file, index=False)
            print(f"📄 Data saved to {excel_file}")
            
            success_count = len([d for d in processed_data if 'error' not in d])
            error_count = len(processed_data) - success_count
            print(f"📊 Statistics: {success_count} successes, {error_count} errors")
            
        except Exception as e:
            print(f"❌ Error saving Excel file: {e}")
    
    except Exception as e:
        print(f"❌ Critical error in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        print("Starting script...")
        start_time = time.time()
        asyncio.run(main())
        end_time = time.time()
        print(f"⏱️  Total time: {end_time - start_time:.2f} seconds")
    except KeyboardInterrupt:
        print("Script interrupted by user")
    except Exception as e:
        print(f"Critical error in script: {e}")
        import traceback
        traceback.print_exc()