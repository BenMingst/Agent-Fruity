#!/usr/bin/env python3
"""
Automated Test Drops for Suika Game
Runs specified number of fruit drops with random x coordinates
"""

import random
import time
from game_interface import SuikaGameInterface

class AutomatedTestDrops:
    def __init__(self, num_drops: int = 10):
        """
        Initialize automated test system
        Args:
            num_drops: Number of fruit drops to simulate
        """
        self.num_drops = num_drops
        self.interface = None
        self.drop_results = []
        
    def generate_random_x_coords(self) -> list:
        """
        Generate random x coordinates between 0.0 and 1.0
        Returns:
            List of random x coordinates
        """
        coords = []
        for i in range(self.num_drops):
            x_coord = random.uniform(0.0, 1.0)
            coords.append(x_coord)
            print(f"Generated drop {i+1}: x={x_coord:.4f}")
        return coords
    
    def run_automated_test(self):
        """
        Run automated test with specified number of drops
        """
        print(f"🚀 Starting automated test with {self.num_drops} fruit drops")
        print("="*60)
        
        # Generate random coordinates
        x_coordinates = self.generate_random_x_coords()
        
        # Initialize game interface
        self.interface = SuikaGameInterface()
        
        try:
            # Setup the game interface
            print("\n🎮 Initializing game interface...")
            if not self.interface.setup_browser():
                return False
            
            if not self.interface.navigate_to_game():
                self.interface.cleanup()
                return False
            
            if not self.interface.setup_screenshot_tool():
                self.interface.cleanup()
                return False
            
            # Wait for game to load
            time.sleep(3)
            
            if not self.interface.get_game_window_bounds():
                self.interface.cleanup()
                return False
            
            if not self.interface.setup_click_detection():
                self.interface.cleanup()
                return False
            
            print("\n✅ Game interface initialized successfully!")
            
            # Take initial screenshot
            print("\n📸 Taking initial screenshot...")
            screenshot = self.interface.capture_screenshot()
            if screenshot is not None:
                if self.interface.analyze_game_state(screenshot):
                    self.interface.score = self.interface.extract_score_from_devtools()
                    self.interface.print_game_status()
            
            # Run automated drops
            print(f"\n🎯 Starting {self.num_drops} automated fruit drops...")
            
            for i, x_coord in enumerate(x_coordinates):
                print(f"\n" + "="*50)
                print(f"🍎 DROP {i+1}/{self.num_drops} - X Coordinate: {x_coord:.4f}")
                print("="*50)
                
                # Execute the automated drop
                success = self.interface.run_automated_drop(x_coord)
                
                # Record result
                result = {
                    'drop_number': i+1,
                    'x_coordinate': x_coord,
                    'success': success,
                    'score': self.interface.score if success else None,
                    'next_fruit': self.interface.next_fruit if success else None
                }
                self.drop_results.append(result)
                
                if success:
                    print(f"✅ Drop {i+1} completed successfully!")
                else:
                    print(f"❌ Drop {i+1} failed!")
                    # Don't break on failure, continue with remaining drops
                    
                # Small delay between drops
                time.sleep(1)
            
            # Print summary
            self.print_test_summary()
            
        except KeyboardInterrupt:
            print("\n🛑 Test interrupted by user!")
        except Exception as e:
            print(f"💥 Automated test error: {e}")
        
        finally:
            # Only cleanup after ALL drops are complete
            print("\n🏁 All drops completed. Closing browser...")
            if self.interface:
                self.interface.cleanup()
    
    def print_test_summary(self):
        """Print summary of all test drops"""
        print("\n" + "🎉" + "="*50 + "🎉")
        print("        AUTOMATED TEST SUMMARY")
        print("="*54)
        
        successful_drops = [r for r in self.drop_results if r['success']]
        failed_drops = [r for r in self.drop_results if not r['success']]
        
        print(f"Total Drops: {len(self.drop_results)}")
        print(f"Successful: {len(successful_drops)}")
        print(f"Failed: {len(failed_drops)}")
        
        if successful_drops:
            final_score = successful_drops[-1]['score']
            print(f"Final Score: {final_score}")
            
            print(f"\nDetailed Results:")
            for result in self.drop_results:
                status = "✅" if result['success'] else "❌"
                score = result['score'] if result['success'] else "N/A"
                next_fruit = result['next_fruit'] if result['success'] else "N/A"
                print(f"  Drop {result['drop_number']}: x={result['x_coordinate']:.4f} {status} Score={score} Next={next_fruit}")
        
        print("="*54)

def main():
    """Main entry point for automated testing"""
    import sys
    
    # Get number of drops from command line or use default
    num_drops = 10
    if len(sys.argv) > 1:
        try:
            num_drops = int(sys.argv[1])
        except ValueError:
            print("Invalid number of drops, using default: 10")
    
    print(f"🎯 Automated Suika Game Test - {num_drops} drops")
    
    # Run the automated test
    test_runner = AutomatedTestDrops(num_drops)
    test_runner.run_automated_test()

if __name__ == "__main__":
    main()