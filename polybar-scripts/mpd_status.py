from mpd import MPDClient
import time

play_icon = ""
pause_icon = ""

def loop(client):
    while True:
        try:
            client.connect("localhost", 6600)
            status = client.status()
            if status['state'] != 'stop':
                song = client.playlistid(status['songid'])[0]
                client.disconnect()
                icon = play_icon if status['state'] == 'play' else pause_icon
                string = "{} {} - {}".format(icon, song['albumartist'], song['title'])
            else:
                string = ""
                client.disconnect()
            print(string)
        except:
            try:
                client.disconnect()
            except:
                pass
        time.sleep(1)
    

if __name__ == "__main__":
    client = MPDClient()
    client.timeout = 10
    client.idletimeout = None
    loop(client)