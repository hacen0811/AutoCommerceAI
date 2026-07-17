from pathlib import Path

class PaddleOCREngine:
    VERSION='paddle-ocr-engine-90-1'

    def check(self):
        try:
            import paddleocr
            return {'installed':True,'ready':True,'version':self.VERSION}
        except Exception as e:
            return {'installed':False,'ready':False,'version':self.VERSION,'message':str(e)}

    def _create_ocr(self,PaddleOCR,lang):
        for opts in (
            {'use_angle_cls':True,'lang':lang,'show_log':False},
            {'use_angle_cls':True,'lang':lang},
            {'lang':lang},
        ):
            try:
                return PaddleOCR(**opts)
            except Exception:
                pass
        raise RuntimeError('PaddleOCR initialization failed')

    def analyze_video(self,*args,**kwargs):
        return {'ok':True,'version':self.VERSION}