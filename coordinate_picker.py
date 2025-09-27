#!/usr/bin/env python3
"""
Simple Coordinate Picker Tool
Step-by-step guided process to select game regions
"""

import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from PIL import Image
import io

class SimpleCoordinatePicker:
    def __init__(self):
        self.regions = {}
        self.step = 0
        self.steps = [
            {'name': 'board', 'title': 'GAME BOARD', 'color': (255, 0, 0), 'instruction': 'Drag around the MAIN GAME BOARD (the big rectangular playing area)'},
            {'name': 'current', 'title': 'CURRENT FRUIT', 'color': (0, 255, 0), 'instruction': 'Drag around the CURRENT FRUIT area (where the fruit hovers before dropping)'},
            {'name': 'next', 'title': 'NEXT FRUIT', 'color': (0, 0, 255), 'instruction': 'Drag around the NEXT FRUIT preview (usually top-right corner)'}
        ]
        self.drawing = False
        self.start_point = None
        self.completed = False
        
    def mouse_callback(self, event, x, y, flags, param):
        img_work, original_img = param
        
        if self.completed:
            return
            
        current_step = self.steps[self.step]
        
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.start_point = (x, y)
            print(f"✓ Started selecting {current_step['title']} at ({x}, {y})")
            
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            # Show live preview while dragging
            img_temp = img_work.copy()
            if self.start_point:
                cv2.rectangle(img_temp, self.start_point, (x, y), current_step['color'], 2)
                self.show_instructions(img_temp)
                cv2.imshow('Coordinate Picker - Follow the steps', img_temp)
                
        elif event == cv2.EVENT_LBUTTONUP and self.drawing:
            self.drawing = False
            end_point = (x, y)
            
            if self.start_point:
                # Calculate rectangle
                x1, y1 = self.start_point
                x2, y2 = end_point
                left, right = min(x1, x2), max(x1, x2)
                top, bottom = min(y1, y2), max(y1, y2)
                
                # Make sure it's a reasonable size
                if (right - left) > 10 and (bottom - top) > 10:
                    self.regions[current_step['name']] = {
                        'left': left, 'right': right, 'top': top, 'bottom': bottom,
                        'width': right - left, 'height': bottom - top
                    }
                    
                    # Draw permanent rectangle
                    cv2.rectangle(img_work, (left, top), (right, bottom), current_step['color'], 3)
                    cv2.putText(img_work, current_step['title'], (left, top-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, current_step['color'], 2)
                    
                    print(f"✓ {current_step['title']} selected: {right-left}x{bottom-top} pixels")
                    
                    # Move to next step
                    self.step += 1
                    if self.step >= len(self.steps):
                        self.completed = True
                        print("\n🎉 ALL REGIONS SELECTED! Press any key to see results...")
                        cv2.putText(img_work, "DONE! Press any key for results", (50, 50),
                                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 3)
                    else:
                        print(f"\n📍 Next: {self.steps[self.step]['instruction']}")
                    
                    self.show_instructions(img_work)
                    cv2.imshow('Coordinate Picker - Follow the steps', img_work)
                else:
                    print("❌ Area too small, try again")
    
    def show_instructions(self, img):
        if self.completed:
            return
            
        current_step = self.steps[self.step]
        
        # Add instruction overlay
        overlay = img.copy()
        cv2.rectangle(overlay, (10, 10), (img.shape[1]-10, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, img, 0.3, 0, img)
        
        # Step counter
        cv2.putText(img, f"STEP {self.step + 1} of {len(self.steps)}", (20, 40),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        # Current instruction
        cv2.putText(img, current_step['instruction'], (20, 70),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, current_step['color'], 2)
        
        # Help text
        cv2.putText(img, "DRAG from corner to corner, then release", (20, 100),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    def get_coordinates(self):
        print("Setting up browser...")
        
        # Setup Chrome browser
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        try:
            print("Navigating to game...")
            driver.get("https://suika.world/play/offline")
            
            # Wait for page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "canvas"))
            )
            
            time.sleep(3)  # Let game fully load
            
            print("Taking screenshot of entire Chrome window...")
            # Take screenshot of entire browser window
            browser_screenshot = driver.get_screenshot_as_png()
            
            # Convert to opencv format
            img = Image.open(io.BytesIO(browser_screenshot))
            img_array = np.array(img)
            
            # Convert RGB to BGR for OpenCV
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            print(f"Full browser screenshot captured: {img_bgr.shape}")
            
            # Get canvas location for reference
            canvas = driver.find_element(By.TAG_NAME, "canvas")
            canvas_location = canvas.location
            canvas_size = canvas.size
            print(f"Canvas location: {canvas_location}, size: {canvas_size}")
            
            # Save original
            cv2.imwrite("coordinate_picker_screenshot.png", img_bgr)
            
            # Create working copy for annotation
            img_work = img_bgr.copy()
            
            # Show initial instructions
            print("\n" + "🎯" + "="*60 + "🎯")
            print("     SIMPLE COORDINATE PICKER")
            print("="*64)
            print("📋 STEPS:")
            print("   1️⃣  Select the GAME BOARD")
            print("   2️⃣  Select the CURRENT FRUIT area")
            print("   3️⃣  Select the NEXT FRUIT preview")
            print("")
            print("🖱️  Just DRAG from corner to corner of each area")
            print("⏭️  The tool will guide you step by step")
            print("="*64)
            
            # Setup window and mouse callback
            cv2.namedWindow('Coordinate Picker - Follow the steps', cv2.WINDOW_NORMAL)
            
            # Show first instruction
            self.show_instructions(img_work)
            cv2.imshow('Coordinate Picker - Follow the steps', img_work)
            cv2.setMouseCallback('Coordinate Picker - Follow the steps', self.mouse_callback, (img_work, img_bgr))
            
            # Wait for user to complete all steps
            while not self.completed:
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q'):
                    print("❌ Cancelled by user")
                    cv2.destroyAllWindows()
                    return
                    
            # Wait for final key press
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            
            # Generate results
            print("\n" + "🎉" + "="*50 + "🎉")
            print("         PERFECT! COORDINATES FOUND")
            print("="*54)
            
            for step_info in self.steps:
                if step_info['name'] in self.regions:
                    region = self.regions[step_info['name']]
                    print(f"\n📍 {step_info['title']}:")
                    print(f"   Size: {region['width']} x {region['height']} pixels")
                    print(f"   Code: {step_info['name']}_region = screenshot[{region['top']}:{region['bottom']}, {region['left']}:{region['right']}]")
            
            print(f"\n" + "📋" + "="*30 + "📋")
            print("   COPY THIS CODE:")
            print("="*34)
            
            for step_info in self.steps:
                if step_info['name'] in self.regions:
                    region = self.regions[step_info['name']]
                    print(f"{step_info['name']}_region = screenshot[{region['top']}:{region['bottom']}, {region['left']}:{region['right']}]")
                    
            print("="*54)
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            driver.quit()

if __name__ == "__main__":
    picker = SimpleCoordinatePicker()
    picker.get_coordinates()