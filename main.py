import cv2
from estados.state_machine import StateMachine

if __name__ == "__main__":
    cv2.namedWindow('Face Paint Demo', cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty('Face Paint Demo', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

sm = StateMachine()
sm.run()                                                            
