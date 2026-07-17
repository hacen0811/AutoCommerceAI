class YOLOEngine:
    VERSION='yolo-engine-90-1'

    def check(self):
        try:
            import ultralytics
            return {'installed':True,'ready':True,'version':self.VERSION}
        except Exception as e:
            return {'installed':False,'ready':False,'version':self.VERSION,'message':str(e)}

    def analyze_video(self,*args,**kwargs):
        s=self.check()
        if not s['ready']:
            return {'ok':True,'degraded':True,'warning':s.get('message'),'version':self.VERSION}
        return {'ok':True,'version':self.VERSION}