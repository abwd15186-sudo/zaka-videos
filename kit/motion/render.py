import asyncio,subprocess,os,sys
from playwright.async_api import async_playwright
async def main():
    os.makedirs('fr',exist_ok=True)
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--allow-file-access-from-files'])
        pg=await b.new_page(viewport={'width':1080,'height':960})
        await pg.goto('file://'+os.path.abspath('lens.html')); await pg.wait_for_timeout(500)
        for i in range(120):
            await pg.evaluate(f'setT({i/30})'); await pg.screenshot(path=f'fr/{i:04d}.png')
        await b.close()
asyncio.run(main())
subprocess.run('ffmpeg -y -loglevel error -framerate 30 -i fr/%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 lens_top.mp4',shell=True)
