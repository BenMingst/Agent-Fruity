#!/usr/bin/env python3
"""
Inspect Suika Game DOM Structure
Analyzes the HTML elements to find proper selectors for game components
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def inspect_game_dom():
    """Inspect the DOM structure of the Suika game"""
    
    # Setup Chrome browser
    chrome_options = Options()
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        print("Navigating to Suika game...")
        driver.get("https://suika.world/play/offline")
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "canvas"))
        )
        
        time.sleep(3)  # Let game fully load
        
        print("\n" + "="*60)
        print("SUIKA GAME DOM STRUCTURE ANALYSIS")
        print("="*60)
        
        # Get page structure
        print("\n1. OVERALL PAGE STRUCTURE:")
        body = driver.find_element(By.TAG_NAME, "body")
        print(f"Body classes: {body.get_attribute('class')}")
        
        # Find all major containers
        containers = driver.find_elements(By.CSS_SELECTOR, "div, section, main, article")
        print(f"Found {len(containers)} container elements")
        
        # Analyze canvas elements
        print("\n2. CANVAS ELEMENTS:")
        canvases = driver.find_elements(By.TAG_NAME, "canvas")
        for i, canvas in enumerate(canvases):
            print(f"Canvas {i+1}:")
            print(f"  - ID: {canvas.get_attribute('id')}")
            print(f"  - Classes: {canvas.get_attribute('class')}")
            print(f"  - Size: {canvas.get_attribute('width')}x{canvas.get_attribute('height')}")
            print(f"  - Position: {canvas.location}")
            print(f"  - Dimensions: {canvas.size}")
        
        # Look for game-specific elements
        print("\n3. GAME UI ELEMENTS:")
        
        # Score elements
        score_selectors = [
            '[class*="score"]', '[id*="score"]', 
            '[class*="point"]', '[id*="point"]',
            'span', 'div'
        ]
        
        for selector in score_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    text = elem.text.strip()
                    if text.isdigit() or 'score' in text.lower():
                        print(f"Potential score element: {selector}")
                        print(f"  - Text: '{text}'")
                        print(f"  - ID: {elem.get_attribute('id')}")
                        print(f"  - Classes: {elem.get_attribute('class')}")
                        print(f"  - Position: {elem.location}")
            except:
                pass
        
        # Fruit display elements  
        print("\n4. FRUIT/PREVIEW ELEMENTS:")
        fruit_selectors = [
            '[class*="fruit"]', '[id*="fruit"]',
            '[class*="next"]', '[id*="next"]',
            '[class*="current"]', '[id*="current"]',
            '[class*="preview"]', '[id*="preview"]'
        ]
        
        for selector in fruit_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements:
                    print(f"Potential fruit element: {selector}")
                    print(f"  - ID: {elem.get_attribute('id')}")
                    print(f"  - Classes: {elem.get_attribute('class')}")
                    print(f"  - Position: {elem.location}")
                    print(f"  - Size: {elem.size}")
            except:
                pass
        
        # Get all elements with IDs
        print("\n5. ALL ELEMENTS WITH IDs:")
        all_elements = driver.find_elements(By.CSS_SELECTOR, "[id]")
        for elem in all_elements:
            elem_id = elem.get_attribute('id')
            if elem_id:
                print(f"  - #{elem_id} ({elem.tag_name})")
        
        # Get all elements with classes
        print("\n6. ALL ELEMENTS WITH CLASSES:")
        all_elements = driver.find_elements(By.CSS_SELECTOR, "[class]")
        class_list = set()
        for elem in all_elements:
            classes = elem.get_attribute('class')
            if classes:
                for cls in classes.split():
                    class_list.add(f".{cls}")
        
        for cls in sorted(class_list):
            print(f"  - {cls}")
        
        # JavaScript inspection
        print("\n7. JAVASCRIPT VARIABLES/OBJECTS:")
        js_vars = driver.execute_script("""
            var gameVars = [];
            for (var prop in window) {
                if (prop.toLowerCase().includes('game') || 
                    prop.toLowerCase().includes('fruit') || 
                    prop.toLowerCase().includes('score') ||
                    prop.toLowerCase().includes('suika')) {
                    gameVars.push(prop + ' = ' + typeof window[prop]);
                }
            }
            return gameVars;
        """)
        
        for var in js_vars:
            print(f"  - {var}")
        
        # Canvas context inspection
        print("\n8. DETAILED CANVAS ANALYSIS:")
        canvas_info = driver.execute_script("""
            var canvas = document.querySelector('canvas');
            if (canvas) {
                var rect = canvas.getBoundingClientRect();
                return {
                    hasContext: !!canvas.getContext,
                    width: canvas.width,
                    height: canvas.height,
                    clientWidth: canvas.clientWidth,
                    clientHeight: canvas.clientHeight,
                    style: canvas.style.cssText,
                    boundingRect: {
                        top: rect.top,
                        left: rect.left,
                        right: rect.right,
                        bottom: rect.bottom,
                        width: rect.width,
                        height: rect.height
                    },
                    offsetTop: canvas.offsetTop,
                    offsetLeft: canvas.offsetLeft,
                    offsetWidth: canvas.offsetWidth,
                    offsetHeight: canvas.offsetHeight
                };
            }
            return null;
        """)
        
        if canvas_info:
            for key, value in canvas_info.items():
                if key == 'boundingRect':
                    print(f"  - {key}:")
                    for subkey, subval in value.items():
                        print(f"    - {subkey}: {subval}")
                else:
                    print(f"  - {key}: {value}")
        
        # Deep dive into fruit preview elements
        print("\n9. FRUIT PREVIEW DETAILED ANALYSIS:")
        fruit_preview_info = driver.execute_script("""
            var results = [];
            
            // Look for next fruit container (picture element)
            var nextFruitContainer = document.querySelector('picture');
            if (nextFruitContainer) {
                var rect = nextFruitContainer.getBoundingClientRect();
                results.push({
                    type: 'next_fruit_container',
                    element: 'picture',
                    rect: rect,
                    classes: nextFruitContainer.className,
                    innerHTML: nextFruitContainer.innerHTML.substring(0, 200)
                });
            }
            
            // Look for fruit image
            var fruitImg = document.querySelector('img.aspect-square.w-full.object-contain');
            if (fruitImg) {
                var rect = fruitImg.getBoundingClientRect();
                results.push({
                    type: 'fruit_image',
                    element: 'img.aspect-square.w-full.object-contain',
                    rect: rect,
                    src: fruitImg.src,
                    alt: fruitImg.alt,
                    classes: fruitImg.className,
                    style: fruitImg.style.cssText
                });
            }
            
            // Look for all images with fruit paths
            var allFruitImgs = document.querySelectorAll('img[src*="fruit"]');
            allFruitImgs.forEach(function(img, index) {
                var rect = img.getBoundingClientRect();
                results.push({
                    type: 'fruit_image_' + index,
                    element: 'img[src*="fruit"]',
                    rect: rect,
                    src: img.src,
                    alt: img.alt,
                    classes: img.className
                });
            });
            
            return results;
        """)
        
        for info in fruit_preview_info:
            print(f"  {info['type']}:")
            print(f"    - element: {info['element']}")
            if 'rect' in info:
                rect = info['rect']
                print(f"    - position: x={rect['x']:.1f}, y={rect['y']:.1f}")
                print(f"    - size: {rect['width']:.1f}x{rect['height']:.1f}")
                print(f"    - bounds: top={rect['top']:.1f}, left={rect['left']:.1f}, right={rect['right']:.1f}, bottom={rect['bottom']:.1f}")
            if 'src' in info:
                print(f"    - src: {info['src']}")
            if 'alt' in info:
                print(f"    - alt: {info['alt']}")
            if 'classes' in info:
                print(f"    - classes: {info['classes']}")
            print()
        
        # Calculate precise game area measurements
        print("\n10. PRECISE GAME AREA MEASUREMENTS:")
        game_measurements = driver.execute_script("""
            var canvas = document.querySelector('canvas');
            var scoreElement = document.querySelector('.score');
            var fruitImg = document.querySelector('img.aspect-square.w-full.object-contain');
            
            var measurements = {};
            
            if (canvas) {
                var canvasRect = canvas.getBoundingClientRect();
                measurements.canvas = {
                    position: canvasRect,
                    actualSize: {width: canvas.width, height: canvas.height},
                    displaySize: {width: canvas.clientWidth, height: canvas.clientHeight}
                };
                
                // Calculate current fruit area relative to canvas (top center region)
                var currentFruitRelative = {
                    topPercent: 0.1,      // 10% from top
                    bottomPercent: 0.25,  // 25% from top
                    leftPercent: 0.35,    // 35% from left
                    rightPercent: 0.65    // 65% from left
                };
                
                measurements.currentFruitArea = {
                    relative: currentFruitRelative,
                    absolute: {
                        top: canvasRect.top + canvasRect.height * currentFruitRelative.topPercent,
                        bottom: canvasRect.top + canvasRect.height * currentFruitRelative.bottomPercent,
                        left: canvasRect.left + canvasRect.width * currentFruitRelative.leftPercent,
                        right: canvasRect.left + canvasRect.width * currentFruitRelative.rightPercent
                    }
                };
                
                // Calculate board area relative to canvas (main play area)
                var boardRelative = {
                    topPercent: 0.2,      // 20% from top
                    bottomPercent: 0.9,   // 90% from top
                    leftPercent: 0.1,     // 10% from left
                    rightPercent: 0.9     // 90% from left
                };
                
                measurements.boardArea = {
                    relative: boardRelative,
                    absolute: {
                        top: canvasRect.top + canvasRect.height * boardRelative.topPercent,
                        bottom: canvasRect.top + canvasRect.height * boardRelative.bottomPercent,
                        left: canvasRect.left + canvasRect.width * boardRelative.leftPercent,
                        right: canvasRect.left + canvasRect.width * boardRelative.rightPercent
                    }
                };
            }
            
            if (scoreElement) {
                measurements.score = scoreElement.getBoundingClientRect();
            }
            
            if (fruitImg) {
                measurements.nextFruitPreview = fruitImg.getBoundingClientRect();
            }
            
            return measurements;
        """)
        
        for area, data in game_measurements.items():
            print(f"  {area}:")
            if area == 'canvas':
                print(f"    - position: {data['position']}")
                print(f"    - actual size: {data['actualSize']}")
                print(f"    - display size: {data['displaySize']}")
            elif area in ['currentFruitArea', 'boardArea']:
                print(f"    - relative percentages: {data['relative']}")
                print(f"    - absolute coordinates: {data['absolute']}")
            else:
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        print(f"    - {key}: {value:.1f}")
                    else:
                        print(f"    - {key}: {value}")
            print()
        
        # Generate cropping coordinates for code
        print("\n11. GENERATED CROPPING COORDINATES:")
        if canvas_info and 'width' in canvas_info and 'height' in canvas_info:
            canvas_w = canvas_info['width']
            canvas_h = canvas_info['height']
            
            print(f"  Canvas dimensions: {canvas_w}x{canvas_h}")
            print(f"  ")
            print(f"  # Current fruit region (top center, 15% down):")
            current_y = int(canvas_h * 0.15)
            print(f"  current_fruit_region = screenshot[{current_y-40}:{current_y+40}, {canvas_w//2-40}:{canvas_w//2+40}]")
            print(f"  ")
            print(f"  # Board region (main play area, 20-90% vertically, 10-90% horizontally):")
            board_top = int(canvas_h * 0.2)
            board_bottom = int(canvas_h * 0.9)
            board_left = int(canvas_w * 0.1)
            board_right = int(canvas_w * 0.9)
            print(f"  board_region = screenshot[{board_top}:{board_bottom}, {board_left}:{board_right}]")
            print(f"  ")
            print(f"  # Region sizes:")
            print(f"  current_fruit_region size: 80x80 pixels")
            print(f"  board_region size: {board_right-board_left}x{board_bottom-board_top} pixels")
        
        print("\n" + "="*60)
        print("DEEP INSPECTION COMPLETE")
        print("="*60)
        
    except Exception as e:
        print(f"Error during inspection: {e}")
    
    finally:
        input("\nPress Enter to close browser...")
        driver.quit()

if __name__ == "__main__":
    inspect_game_dom()