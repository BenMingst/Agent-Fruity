#!/usr/bin/env python3
"""
Suika Game Interface
Automates browser interaction, captures screen, analyzes game state, and extracts game information.
"""

import time
import numpy as np
import cv2
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import mss
from typing import List, Optional


class SuikaGameInterface:
    # Configuration
    WAIT_AFTER_DROP = 1.0  # Seconds to wait after fruit drop
    COLOR_TOLERANCE = 40   # Color matching tolerance
    BG_TOLERANCE = 16      # Background color tolerance
    
    def __init__(self):
        """Initialize the Suika Game Interface"""
        self.driver = None
        self.screenshot_tool = None
        self.score = 0
        
        # Create debug output folder
        self.debug_folder = "test_output"
        if not os.path.exists(self.debug_folder):
            os.makedirs(self.debug_folder)
            print(f"[OK] Created debug folder: {self.debug_folder}")
        
        # Fruit colors as numpy array for efficient processing
        self.fruit_colors = np.array([
            [224, 50, 50],    # 0: Cherry (red)
            [245, 90, 76],    # 1: Strawberry (red-pink)
            [163, 107, 253],  # 2: Grape (purple)
            [253, 186, 1],    # 3: Lemon (yellow)
            [254, 137, 23],   # 4: Orange (orange)
            [245, 21, 21],    # 5: Apple (red)
            [253, 245, 106],  # 6: Pear (yellow-green)
            [255, 190, 177],  # 7: Peach (peach)
            [246, 229, 11],   # 8: Pineapple (yellow)
            [154, 217, 16],   # 9: Melon (green)
            [82, 161, 36],    # 10: Watermelon (dark green)
        ])
        
        # Fruit names for display
        self.fruit_names = [
            "Cherry",      # 0
            "Strawberry",  # 1
            "Grape",       # 2
            "Lemon",       # 3
            "Orange",      # 4
            "Apple",       # 5
            "Pear",        # 6
            "Peach",       # 7
            "Pineapple",   # 8
            "Melon",       # 9
            "Watermelon"   # 10
        ]
        
        # Game state variables
        self.next_fruit = -1
        self.board_state = []
        
        # Background colors to filter out
        self.background_colors = np.array([
            [255, 172, 170],  # #ffacaa
            [234, 159, 157],  # #ea9f9d
        ])
        
    def setup_browser(self) -> bool:
        """Set up Chrome browser"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            print("[OK] Browser setup complete")
            return True
            
        except Exception as e:
            print(f"[ERROR] Browser setup failed: {e}")
            return False
    
    def navigate_to_game(self) -> bool:
        """
        Navigate to the Suika game URL
        Returns True if successful, False otherwise
        """
        try:
            self.driver.get("https://suika.world/play/offline")
            
            # Wait for the page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "canvas"))
            )
            
            print("[OK] Successfully navigated to Suika game")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to navigate to game: {e}")
            return False
    
    def setup_screenshot_tool(self) -> bool:
        """
        Initialize the screenshot capture tool
        Returns True if successful, False otherwise
        """
        try:
            self.screenshot_tool = mss.mss()
            print("[OK] Screenshot tool initialized")
            return True
            
        except Exception as e:
            print(f"[ERROR] Screenshot tool setup failed: {e}")
            return False
    
    
    def capture_screenshot(self) -> Optional[np.ndarray]:
        """
        Capture screenshot of the entire browser window
        Returns numpy array of the screenshot or None if failed
        """
        try:
            # Use full browser screenshot to match coordinate picker
            browser_screenshot = self.driver.get_screenshot_as_png()
            
            # Convert PNG bytes to numpy array
            import io
            from PIL import Image
            img = Image.open(io.BytesIO(browser_screenshot))
            img_array = np.array(img)
            
            # Convert RGB to BGR for OpenCV
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            
            return img_bgr
            
        except Exception as e:
            print(f"[ERROR] Browser screenshot failed: {e}")
            return None
    
    def get_next_fruit_from_dom(self) -> int:
        """
        Extract next fruit by finding the img element with fruit source
        Returns fruit index or -1 if not found
        """
        try:
            # Find the next fruit image element
            next_fruit_img = self.driver.find_element(By.CSS_SELECTOR, "img.aspect-square.w-full.object-contain")
            src = next_fruit_img.get_attribute("src")
            alt = next_fruit_img.get_attribute("alt")
            
            
            # Map fruit names to indices
            fruit_mapping = {
                "cherry": 0, "strawberry": 1, "grape": 2, "lemon": 3,
                "orange": 4, "apple": 5, "pear": 6, "peach": 7,
                "pineapple": 8, "melon": 9, "watermelon": 10
            }
            
            # Extract fruit name from src or alt
            if alt:
                fruit_name = alt.lower()
                return fruit_mapping.get(fruit_name, -1)
            elif src and "/fruit/" in src:
                # Extract from path like "/fruit/grape.png"
                fruit_name = src.split("/fruit/")[1].split(".")[0].lower()
                return fruit_mapping.get(fruit_name, -1)
            
            return -1
            
        except Exception as e:
            print(f"[ERROR] Next fruit DOM extraction failed: {e}")
            return -1
    
    def save_debug_regions(self, screenshot: np.ndarray, next_region: np.ndarray, board_region: np.ndarray):
        """Save essential debug images"""
        try:
            timestamp = str(int(time.time()))
            cv2.imwrite(f"{self.debug_folder}/screenshot_{timestamp}.png", screenshot)
            cv2.imwrite(f"{self.debug_folder}/board_50x50_{timestamp}.png",
                       cv2.resize(board_region, (50, 50), interpolation=cv2.INTER_AREA))
        except Exception as e:
            print(f"[ERROR] Debug save failed: {e}")
    
    def extract_score_from_devtools(self) -> int:
        """
        Extract the current score using the .score class selector
        Returns the score or 0 if failed
        """
        try:
            # Use the specific .score class we found
            score_element = self.driver.find_element(By.CSS_SELECTOR, ".score")
            score_text = score_element.text.strip()
            
            
            # Extract numeric value
            score = int(score_text) if score_text.isdigit() else 0
            return score
            
        except Exception as e:
            print(f"[ERROR] Score extraction failed: {e}")
            return 0
    
    
    def analyze_game_state(self, screenshot: np.ndarray) -> bool:
        """Analyze screenshot to determine game state"""
        try:
            if screenshot is None:
                return False
            
            # Extract game regions
            board_region = screenshot[538:1125, 572:1115]
            next_fruit_region = screenshot[506:715, 1260:1491]
            
            # Get next fruit from DOM and analyze board
            self.next_fruit = self.get_next_fruit_from_dom()
            self.board_state = self.scan_board_state_improved(board_region)
            self.save_debug_regions(screenshot, next_fruit_region, board_region)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Game state analysis failed: {e}")
            return False
    
    
    def scan_board_state_improved(self, board_image: np.ndarray) -> List[List[int]]:
        """
        Simple, accurate vectorized color matching
        """
        try:
            if board_image.size == 0:
                return []
            
            height, width = board_image.shape[:2]
            size = min(height, width)
            start_y = (height - size) // 2
            start_x = (width - size) // 2
            square_board = board_image[start_y:start_y+size, start_x:start_x+size]
            
            # Resize to 50x50 and convert to RGB
            resized_board = cv2.resize(square_board, (50, 50), interpolation=cv2.INTER_AREA)
            board_rgb = cv2.cvtColor(resized_board, cv2.COLOR_BGR2RGB)
            
            # Simple vectorized color matching (fast and accurate)
            board_flat = board_rgb.reshape(-1, 3)
            
            # Background filtering
            bg_distances = np.sqrt(np.sum((board_flat[:, None, :] - self.background_colors[None, :, :]) ** 2, axis=2))
            is_background = np.min(bg_distances, axis=1) <= self.BG_TOLERANCE
            
            # Fruit color matching
            fruit_distances = np.sqrt(np.sum((board_flat[:, None, :] - self.fruit_colors[None, :, :]) ** 2, axis=2))
            closest_fruits = np.argmin(fruit_distances, axis=1)
            min_fruit_distances = np.min(fruit_distances, axis=1)
            
            # Apply filters
            closest_fruits[is_background | (min_fruit_distances > self.COLOR_TOLERANCE)] = -1
            board_2d = closest_fruits.reshape(50, 50)
            
            # Simple fix: Remove full-height vertical lines of any single fruit (likely background)
            for col in range(50):
                column = board_2d[:, col]
                unique, counts = np.unique(column[column >= 0], return_counts=True)
                if len(unique) == 1 and counts[0] > 35:  # Single fruit type spanning >70% of column
                    board_2d[:, col][board_2d[:, col] == unique[0]] = -1
            
            return board_2d.tolist()
            
        except Exception as e:
            print(f"[ERROR] Board scanning failed: {e}")
            return []

    def print_game_status(self):
        """Print current game status with board visualization"""
        next_name = self.fruit_names[self.next_fruit] if 0 <= self.next_fruit < len(self.fruit_names) else "Unknown"
        
        print(f"\n🎮 Score: {self.score} | Next: {self.next_fruit} = {next_name}")
        
        if self.board_state:
            print(f"\nBoard State (50x50):")
            # Show fruit legend compactly
            print("Legend: " + " | ".join([f"{i}={name}" for i, name in enumerate(self.fruit_names)]) + " | -1=Empty")
            
            # Print board with row markers every 10 rows
            for i, row in enumerate(self.board_state):
                if i % 10 == 0:
                    print(f"\nRow {i:2d}: ", end="")
                else:
                    print("       ", end="")
                
                # Print row compactly
                row_str = "".join([f"{cell:2d}" if cell >= 0 else " ." for cell in row])
                print(row_str)
        else:
            print("Board state not available")
        
        print("-" * 50)
    
    def setup_click_detection(self) -> bool:
        """
        Set up JavaScript click detection on the game canvas
        Returns True if successful, False otherwise
        """
        try:
            # Add JavaScript to detect clicks on the canvas
            click_detection_script = """
            window.gameClicked = false;
            let canvas = document.querySelector('canvas');
            if (canvas) {
                canvas.addEventListener('click', function() {
                    window.gameClicked = true;
                });
                return true;
            }
            return false;
            """
            
            result = self.driver.execute_script(click_detection_script)
            if result:
                print("[OK] Click detection initialized on game canvas")
                return True
            else:
                print("[ERROR] Could not find game canvas for click detection")
                return False
                
        except Exception as e:
            print(f"[ERROR] Click detection setup failed: {e}")
            return False
    
    def check_for_click(self) -> bool:
        """
        Check if a click has occurred on the game canvas
        Returns True if a click was detected, False otherwise
        """
        try:
            # Check if a click occurred and reset the flag
            result = self.driver.execute_script("""
                if (window.gameClicked) {
                    window.gameClicked = false;
                    return true;
                }
                return false;
            """)
            return result
            
        except Exception as e:
            print(f"[ERROR] Click detection check failed: {e}")
            return False

    def run_game_interface(self):
        """Main function to run the game interface"""
        print("Starting Suika Game Interface...")
        
        # Setup sequence
        if not self.setup_browser():
            return False
        
        if not self.navigate_to_game():
            self.cleanup()
            return False
        
        if not self.setup_screenshot_tool():
            self.cleanup()
            return False
        
        # Wait a moment for the game to fully load
        time.sleep(3)
        
        if not self.setup_click_detection():
            self.cleanup()
            return False
        
        print("\n[OK] All systems initialized. Starting game monitoring...")
        
        # Take initial screenshot and analyze
        print("\nTaking initial screenshot...")
        screenshot = self.capture_screenshot()
        if screenshot is not None:
            if self.analyze_game_state(screenshot):
                self.score = self.extract_score_from_devtools()
                self.print_game_status()
        
        print("\n🎯 Ready! Click on the game to drop a fruit...")
        print(f"📸 Screenshots will be taken {self.WAIT_AFTER_DROP} seconds after each fruit drop")
        
        try:
            # Main monitoring loop - wait for clicks on the game
            while True:
                # Check for clicks every 100ms to be responsive
                if self.check_for_click():
                    print("\n🍎 Fruit drop detected!")
                    print(f"⏳ Waiting {self.WAIT_AFTER_DROP} seconds for animation to complete...")
                    
                    # Wait for drop animation to complete
                    time.sleep(self.WAIT_AFTER_DROP)
                    
                    print("📸 Taking screenshot now...")
                    # Capture screenshot and analyze
                    screenshot = self.capture_screenshot()
                    
                    if screenshot is not None:
                        # Analyze game state
                        if self.analyze_game_state(screenshot):
                            # Extract score
                            self.score = self.extract_score_from_devtools()
                            
                            # Print status to terminal
                            self.print_game_status()
                    
                    print("\n✅ Analysis complete. Ready for next fruit drop...")
                
                # Small delay to avoid excessive CPU usage
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\nGame monitoring stopped by user.")
        except Exception as e:
            print(f"\n\nUnexpected error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("[OK] Browser closed")
            except:
                pass
        
        if self.screenshot_tool:
            try:
                self.screenshot_tool.close()
                print("[OK] Screenshot tool closed")
            except:
                pass


def main():
    """Main entry point"""
    interface = SuikaGameInterface()
    interface.run_game_interface()


if __name__ == "__main__":
    main()