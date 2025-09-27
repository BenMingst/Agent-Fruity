#!/usr/bin/env python3
"""
Suika Game Interface
Automates browser interaction, captures screen, analyzes game state, and extracts game information.
"""

import time
import json
import numpy as np
import cv2
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import mss
import mss.tools
from typing import List, Tuple, Optional, Dict, Any


class SuikaGameInterface:
    def __init__(self):
        """Initialize the Suika Game Interface"""
        self.driver = None
        self.screenshot_tool = None
        self.game_window_bounds = None
        self.score = 0
        
        # Create debug output folder
        self.debug_folder = "test_output"
        if not os.path.exists(self.debug_folder):
            os.makedirs(self.debug_folder)
            print(f"[OK] Created debug folder: {self.debug_folder}")
        
        # Fruit_ID 2D array - RGB values for each of the 11 fruits (Suika game)
        self.Fruit_ID = [
            [224, 50, 50],    # 0: Cherry (red)
            [245, 90, 76],    # 1: Strawberry (red-pink)
            [163, 107, 253],  # 2: Grape (purple)
            [253, 186, 1],    # 3: Lemon (yellow)
            [254, 137, 23],   # 4: Orange (orange)
            [245, 21, 21],    # 5: Apple (red)
            [253, 245, 106],  # 6: Pear (yellow-green)
            [253, 186, 175],  # 7: Peach (peach)
            [246, 229, 11],   # 8: Pineapple (yellow)
            [154, 217, 16],   # 9: Melon (green)
            [82, 161, 36],    # 10: Watermelon (dark green)
        ]
        
        # Convert to numpy array for easier processing
        self.fruit_colors = np.array(self.Fruit_ID)
        
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
        
        # Background colors to ignore (hex converted to RGB)
        self.background_colors_board_and_next = [
            (255, 172, 170),  # #ffacaa
            (234, 159, 157),  # #ea9f9d
        ]
        
        self.background_colors_next_only = [
            (8, 195, 0),      # #08c300
            (173, 239, 0),    # #adef00
            (49, 203, 45),    # #31cb2d
            (2, 161, 83),     # #02a153
            (36, 113, 40),    # #247128
        ]
        
    def setup_browser(self) -> bool:
        """
        Set up Chrome browser with DevTools Protocol enabled
        Returns True if successful, False otherwise
        """
        try:
            chrome_options = Options()
            chrome_options.add_argument("--enable-automation")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--remote-debugging-port=9222")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Initialize the Chrome driver
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
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
    
    def get_game_window_bounds(self) -> bool:
        """
        Determine the bounds of the game window for accurate screenshot capture
        Returns True if successful, False otherwise
        """
        try:
            # Get browser window position and size
            window_rect = self.driver.get_window_rect()
            
            # Find the canvas element (game area)
            canvas = self.driver.find_element(By.TAG_NAME, "canvas")
            canvas_location = canvas.location
            canvas_size = canvas.size
            
            print(f"[DEBUG] Window rect: {window_rect}")
            print(f"[DEBUG] Canvas location: {canvas_location}")
            print(f"[DEBUG] Canvas size: {canvas_size}")
            
            # Calculate absolute position of the game canvas on screen
            # Need to account for browser chrome/toolbar height
            browser_chrome_height = 100  # Approximate height of address bar + tabs
            
            self.game_window_bounds = {
                "top": window_rect["y"] + canvas_location["y"] + browser_chrome_height,
                "left": window_rect["x"] + canvas_location["x"],
                "width": canvas_size["width"],
                "height": canvas_size["height"]
            }
            
            print(f"[OK] Game window bounds determined: {self.game_window_bounds}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to determine game window bounds: {e}")
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
            
            print(f"[DEBUG] Captured browser screenshot: {img_bgr.shape}")
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
            
            print(f"[DEBUG] Next fruit src: {src}")
            print(f"[DEBUG] Next fruit alt: {alt}")
            
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
    
    def save_debug_regions(self, screenshot: np.ndarray, current_region: np.ndarray,
                          next_region: np.ndarray, board_region: np.ndarray, timestamp: str = None):
        """
        Save cropped regions as debug images to help with calibration
        """
        try:
            if timestamp is None:
                timestamp = str(int(time.time()))
            
            # Save all debug images with timestamp
            cv2.imwrite(f"{self.debug_folder}/full_screenshot_{timestamp}.png", screenshot)
            cv2.imwrite(f"{self.debug_folder}/current_fruit_region_{timestamp}.png", current_region)
            cv2.imwrite(f"{self.debug_folder}/next_fruit_region_{timestamp}.png", next_region)
            cv2.imwrite(f"{self.debug_folder}/board_region_original_{timestamp}.png", board_region)
            
            # Save with detailed info overlay
            height, width = screenshot.shape[:2]
            debug_img = screenshot.copy()
            
            # Draw rectangles showing REFINED USER-SELECTED crop regions
            # Board region: [538:1125, 572:1115]
            cv2.rectangle(debug_img, (572, 538), (1115, 1125), (255, 0, 0), 3)
            
            # Next fruit region: [506:715, 1260:1491]
            cv2.rectangle(debug_img, (1260, 506), (1491, 715), (0, 0, 255), 3)
            
            # Add text labels
            cv2.putText(debug_img, "BOARD (REFINED)", (572, 533), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            cv2.putText(debug_img, "NEXT (REFINED)", (1260, 501), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.putText(debug_img, f"Screenshot: {width}x{height}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imwrite(f"{self.debug_folder}/annotated_screenshot_{timestamp}.png", debug_img)
            
            print(f"[DEBUG] Saved debug images to {self.debug_folder}/ with timestamp {timestamp}")
            print(f"[DEBUG] Screenshot dimensions: {width}x{height}")
            print(f"[DEBUG] Current fruit region: {current_region.shape if current_region.size > 0 else 'Empty'}")
            print(f"[DEBUG] Next fruit region: {next_region.shape if next_region.size > 0 else 'Empty'}")
            print(f"[DEBUG] Board region: {board_region.shape if board_region.size > 0 else 'Empty'}")
            
        except Exception as e:
            print(f"[ERROR] Failed to save debug images: {e}")
    
    def extract_score_from_devtools(self) -> int:
        """
        Extract the current score using the .score class selector
        Returns the score or 0 if failed
        """
        try:
            # Use the specific .score class we found
            score_element = self.driver.find_element(By.CSS_SELECTOR, ".score")
            score_text = score_element.text.strip()
            
            print(f"[DEBUG] Score element text: '{score_text}'")
            
            # Extract numeric value
            score = int(score_text) if score_text.isdigit() else 0
            return score
            
        except Exception as e:
            print(f"[ERROR] Score extraction failed: {e}")
            return 0
    
    def detect_fruit_by_rgb(self, rgb_values: np.ndarray, tolerance: int = 30) -> int:
        """
        Detect fruit type based on RGB values
        Args:
            rgb_values: RGB values to match
            tolerance: Color matching tolerance
        Returns:
            Fruit index (0-9) or -1 if no match found
        """
        try:
            # Calculate distance to each fruit color
            distances = np.sqrt(np.sum((self.fruit_colors - rgb_values) ** 2, axis=1))
            
            # Find the closest match
            closest_match = np.argmin(distances)
            
            # Check if the match is within tolerance
            if distances[closest_match] <= tolerance:
                return closest_match
            else:
                return -1  # No match found
                
        except Exception as e:
            print(f"[ERROR] Fruit detection failed: {e}")
            return -1
    
    def analyze_game_state(self, screenshot: np.ndarray) -> bool:
        """
        Analyze the screenshot to determine game state with improved cropping
        Args:
            screenshot: Game screenshot as numpy array
        Returns:
            True if analysis successful, False otherwise
        """
        try:
            if screenshot is None:
                return False
            
            height, width = screenshot.shape[:2]
            
            # Using REFINED coordinates from coordinate picker tool
            # Board region: Main game board area
            board_region = screenshot[538:1125, 572:1115]
            
            # Next fruit region: Preview area for next fruit
            next_fruit_region = screenshot[506:715, 1260:1491]
            
            print(f"[DEBUG] Browser screenshot dimensions: {width}x{height}")
            print(f"[DEBUG] Board region: [538:1125, 572:1115] = {1115-572}x{1125-538} pixels")
            print(f"[DEBUG] Next fruit region: [506:715, 1260:1491] = {1491-1260}x{715-506} pixels")
            
            # Get next fruit from DOM instead of screenshot
            self.next_fruit = self.get_next_fruit_from_dom()
            
            # Create dummy current fruit region for debug compatibility
            dummy_current_region = screenshot[0:50, 0:50]
            
            # Save debug images to help with calibration
            self.save_debug_regions(screenshot, dummy_current_region, next_fruit_region, board_region)
            
            # Detect next fruit from the cropped region as backup
            next_fruit_detected = self.detect_fruit_in_region(next_fruit_region, region_type="next")
            if self.next_fruit == -1:  # If DOM detection failed, use image detection
                self.next_fruit = next_fruit_detected
            
            # Analyze board state with improved scanning
            self.board_state = self.scan_board_state_improved(board_region)
            
            return True
            
        except Exception as e:
            print(f"[ERROR] Game state analysis failed: {e}")
            return False
    
    def detect_fruit_in_region(self, region: np.ndarray, region_type: str = "current") -> int:
        """
        Detect fruit in a specific region using pixel-by-pixel analysis with background filtering
        Args:
            region: Image region to analyze
            region_type: "board", "next", or "current" - affects background filtering
        Returns:
            Fruit index (0-9) or -1 if no match found
        """
        try:
            if region.size == 0:
                return -1
            
            # Convert BGR to RGB for proper color matching
            region_rgb = cv2.cvtColor(region, cv2.COLOR_BGR2RGB)
            
            # Analyze each pixel and find the most common fruit color
            height, width = region_rgb.shape[:2]
            fruit_votes = [0] * len(self.fruit_colors)
            total_non_background_pixels = 0
            
            for y in range(height):
                for x in range(width):
                    pixel_rgb = region_rgb[y, x]
                    
                    # Skip background colors
                    if self.is_background_color(pixel_rgb, region_type):
                        continue
                        
                    total_non_background_pixels += 1
                    
                    # Check if this pixel matches any fruit color
                    for fruit_idx, fruit_color in enumerate(self.fruit_colors):
                        # Calculate color distance
                        distance = np.sqrt(np.sum((pixel_rgb - fruit_color) ** 2))
                        
                        # If pixel is close enough to this fruit color, vote for it
                        if distance <= 50:  # Tolerance threshold
                            fruit_votes[fruit_idx] += 1
            
            # Return the fruit with the most votes, if significant enough
            max_votes = max(fruit_votes)
            if total_non_background_pixels > 0 and max_votes > (total_non_background_pixels * 0.1):  # At least 10% of non-background pixels match
                return fruit_votes.index(max_votes)
            else:
                return -1
                
        except Exception as e:
            print(f"[ERROR] Region fruit detection failed: {e}")
            return -1
    
    def scan_board_state_improved(self, board_image: np.ndarray) -> List[List[int]]:
        """
        Scan board as 50x50 pixel grid with fruit detection
        Args:
            board_image: Image of the game board
        Returns:
            2D list representing 50x50 board state with fruit indices
        """
        try:
            if board_image.size == 0:
                return []
            
            height, width = board_image.shape[:2]
            
            # Make the board region square by taking the smaller dimension
            size = min(height, width)
            start_y = (height - size) // 2
            start_x = (width - size) // 2
            square_board = board_image[start_y:start_y+size, start_x:start_x+size]
            
            # Resize to exactly 50x50 pixels
            resized_board = cv2.resize(square_board, (50, 50), interpolation=cv2.INTER_AREA)
            
            # Convert BGR to RGB for proper color matching
            board_rgb = cv2.cvtColor(resized_board, cv2.COLOR_BGR2RGB)
            
            # Save the 50x50 debug image with timestamp
            timestamp = str(int(time.time()))
            cv2.imwrite(f"{self.debug_folder}/board_50x50_{timestamp}.png", resized_board)
            cv2.imwrite(f"{self.debug_folder}/board_square_{timestamp}.png", square_board)
            
            print(f"[DEBUG] Board processing:")
            print(f"[DEBUG] Original board region: {board_image.shape}")
            print(f"[DEBUG] Square board: {square_board.shape}")
            print(f"[DEBUG] Resized 50x50: {resized_board.shape}")
            
            # Analyze each pixel in the 50x50 grid
            board_state = []
            
            for row in range(50):
                board_row = []
                for col in range(50):
                    pixel_rgb = board_rgb[row, col]
                    
                    # Find the closest fruit color
                    fruit_id = self.detect_fruit_by_pixel(pixel_rgb)
                    board_row.append(fruit_id)
                
                board_state.append(board_row)
            
            return board_state
            
        except Exception as e:
            print(f"[ERROR] 50x50 board state scanning failed: {e}")
            return []
    
    def is_background_color(self, pixel_rgb: np.ndarray, region_type: str = "board", tolerance: int = 30) -> bool:
        """
        Check if a pixel is a background color that should be ignored
        Args:
            pixel_rgb: RGB values of the pixel
            region_type: "board", "next", or "current"
            tolerance: Color matching tolerance
        Returns:
            True if pixel should be ignored, False otherwise
        """
        try:
            # Colors to ignore for board and next fruit regions
            colors_to_check = self.background_colors_board_and_next.copy()
            
            # Add additional colors for next fruit region only
            if region_type == "next":
                colors_to_check.extend(self.background_colors_next_only)
            
            # Check if pixel matches any background color
            for bg_color in colors_to_check:
                distance = np.sqrt(np.sum((pixel_rgb - bg_color) ** 2))
                if distance <= tolerance:
                    return True
                    
            return False
            
        except Exception as e:
            print(f"[ERROR] Background color check failed: {e}")
            return False
    
    def detect_fruit_by_pixel(self, pixel_rgb: np.ndarray, region_type: str = "board") -> int:
        """
        Detect fruit type for a single pixel with background filtering
        Args:
            pixel_rgb: RGB values of the pixel
            region_type: "board", "next", or "current" - affects background filtering
        Returns:
            Fruit index (0-10) or -1 if no match found
        """
        try:
            # Check if this is a background color to ignore
            if self.is_background_color(pixel_rgb, region_type):
                return -1
            
            # Calculate distance to each fruit color
            distances = np.sqrt(np.sum((self.fruit_colors - pixel_rgb) ** 2, axis=1))
            
            # Find the closest match
            closest_match = np.argmin(distances)
            
            # Check if the match is within tolerance (stricter for single pixels)
            if distances[closest_match] <= 40:  # Tighter tolerance for pixel-level detection
                return closest_match
            else:
                return -1  # No match found
                
        except Exception as e:
            print(f"[ERROR] Pixel fruit detection failed: {e}")
            return -1
    
    def print_game_status(self):
        """Print current game status to terminal with fruit names"""
        print("\n" + "="*70)
        print("SUIKA GAME STATUS")
        print("="*70)
        print(f"Score: {self.score}")
        
        # Print only next fruit with name
        next_name = self.fruit_names[self.next_fruit] if 0 <= self.next_fruit < len(self.fruit_names) else "Unknown"
        
        print(f"Next Fruit: {self.next_fruit} = {next_name}")
        
        print("\nBoard State (50x50 grid):")
        
        if self.board_state:
            # Print fruit legend
            print("\nFruit Legend:")
            for i, name in enumerate(self.fruit_names):
                print(f"  {i} = {name}")
            print("  -1 = Empty/Background")
            
            print(f"\n50x50 Board Grid:")
            for i, row in enumerate(self.board_state):
                if i % 5 == 0:  # Print row numbers every 5 rows for reference
                    print(f"Row {i:2d}: ", end="")
                else:
                    print("       ", end="")
                
                # Print the row with proper spacing
                row_str = ""
                for cell in row:
                    if cell >= 0:
                        row_str += f"{cell:2d}"
                    else:
                        row_str += " ."
                print(row_str)
                
                if i % 10 == 9:  # Add separator every 10 rows
                    print()
        else:
            print("Board state not available")
        
        print("="*70)
    
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
        
        if not self.get_game_window_bounds():
            self.cleanup()
            return False
        
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
        print("📸 Screenshots will be taken ONLY 2 seconds after each fruit drop")
        
        try:
            # Main monitoring loop - wait for clicks on the game
            while True:
                # Check for clicks every 100ms to be responsive
                if self.check_for_click():
                    print("\n🍎 Fruit drop detected!")
                    print("⏳ Waiting exactly 2 seconds for animation to complete...")
                    
                    # Wait EXACTLY 2 seconds for the drop animation to complete
                    time.sleep(2.0)
                    
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