from ultralytics import YOLO

# Windows'ta multiprocessing çökmesini engelleyen güvenlik kapısı
if __name__ == '__main__':
    
    # Kendi seçtiğin model (Harika seçim!)
    model = YOLO('yolo26n-cls.pt') 

    # Eğitimi başlat
    results = model.train(
        data='datasets/yolo_food101', 
        epochs=20,          
        imgsz=224,          
        device='0'        
    )