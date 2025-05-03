import json
import pymem
import pymem.process


def w2s(mtx, posx, posy, posz, width, height):
    screenW = mtx[12]*posx + mtx[13]*posy + mtx[14]*posz + mtx[15]
    if screenW > 0.001:
        screenX = mtx[0]*posx + mtx[1]*posy + mtx[2]*posz + mtx[3]
        screenY = mtx[4]*posx + mtx[5]*posy + mtx[6]*posz + mtx[7]
        camX = width / 2
        camY = height / 2
        x = camX + (camX * screenX / screenW) // 1
        y = camY - (camY * screenY / screenW) // 1
        return [x, y]
    return [-999, -999]


class Cheat:
    def __init__(self):
        with open("data\\client_dll.json", "r") as client_file:
            with open("data\\offsets.json", "r") as offset_file:
                self.client_dll = json.load(client_file)
                self.offsets = json.load(offset_file)

        self.pm = pymem.Pymem("cs2.exe")

        self.client = pymem.process.module_from_name(self.pm.process_handle, "client.dll").lpBaseOfDll
        self.dwLocalPlayerController = self.pm.read_longlong(self.client+ self.offsets["client.dll"]["dwLocalPlayerController"])
        self.dwLocalPlayerPawn = self.pm.read_longlong(self.client + self.offsets["client.dll"]["dwLocalPlayerPawn"])
        self.dwViewMatrix = self.offsets['client.dll']['dwViewMatrix']

        self.m_iszPlayerName = self.client_dll["client.dll"]["classes"]["CBasePlayerController"]["fields"]["m_iszPlayerName"]
        self.m_hPlayerPawn = self.client_dll["client.dll"]["classes"]["CCSPlayerController"]["fields"]["m_hPlayerPawn"]
        self.m_iTeamNum = self.client_dll["client.dll"]["classes"]["C_BaseEntity"]["fields"]["m_iTeamNum"]
        self.m_lifeState = self.client_dll["client.dll"]["classes"]["C_BaseEntity"]["fields"]["m_lifeState"]
        self.m_iHealth = self.client_dll["client.dll"]["classes"]["C_BaseEntity"]["fields"]["m_iHealth"]
        self.m_vOldOrigin = self.client_dll["client.dll"]["classes"]["C_BasePlayerPawn"]["fields"]["m_vOldOrigin"]
        self.m_pGameSceneNode = self.client_dll['client.dll']['classes']['C_BaseEntity']['fields']['m_pGameSceneNode']
        self.m_modelState = self.client_dll['client.dll']['classes']['CSkeletonInstance']['fields']['m_modelState']
        self.m_angEyeAngles = self.client_dll["client.dll"]["classes"]["C_CSPlayerPawnBase"]["fields"]["m_angEyeAngles"]
    def iterate_entities(self):
        ENTITY_ENTRY_SIZE = 120
        ENTITY_COUNT = 64
        self.info = []
        try:
            ent_list_ptr = self.pm.read_longlong(self.client + self.offsets["client.dll"]["dwEntityList"])
        except Exception as e:
            print(f"Error reading entity list: {e}")
            return []
        for i in range(1, ENTITY_COUNT  + 1):
            try:
                list_index = (i & 0x7FFF) >> 9
                entity_index = i & 0x1FF
                entry_ptr = self.pm.read_longlong(ent_list_ptr + (8 * list_index) + 16)
                if not entry_ptr:
                    continue

                controller_ptr = self.pm.read_longlong(entry_ptr + ENTITY_ENTRY_SIZE * entity_index)
                if not controller_ptr:
                    continue

                if controller_ptr == self.dwLocalPlayerController:
                    name = self.pm.read_string(controller_ptr + self.m_iszPlayerName)
                    if not name:
                        continue
                
                    self.info.append({"Id":i, "Name":name, "Controller":controller_ptr, "Pawn":self.dwLocalPlayerPawn})
                    self.LocalPosInArr = len(self.info) - 1
                    self.LocalId = i
                    continue
                
                name = self.pm.read_string(controller_ptr + self.m_iszPlayerName)
                if not name:
                    continue

                controller_pawn_ptr = self.pm.read_longlong(controller_ptr + self.m_hPlayerPawn)
                if not controller_pawn_ptr:
                    continue

                list_entry_ptr = self.pm.read_longlong(ent_list_ptr + 8 * ((controller_pawn_ptr & 0x7FFF) >> 9) + 16)
                if not list_entry_ptr:
                    continue

                pawn_ptr = self.pm.read_longlong(list_entry_ptr + ENTITY_ENTRY_SIZE * (controller_pawn_ptr & 0x1FF))
                if not pawn_ptr:
                    continue
                self.info.append({"Id":i, "Name":name, "Controller":controller_ptr, "Pawn":pawn_ptr})
            except Exception as e:
                print(f"Error iterating entity {i}: {e}")
                continue
        return self.info
    def get_TeamNum(self, i : int):
        team = self.pm.read_uchar(self.info[i]["Pawn"] + self.m_iTeamNum)
        self.info[i]["TeamNum"] = team
    def get_lifeState(self, i : int):
        life = self.pm.read_uchar(self.info[i]["Pawn"] + self.m_lifeState)
        self.info[i]["LifeState"] = life
    def get_Health(self, i : int):
        health = self.pm.read_int(self.info[i]["Pawn"] + self.m_iHealth)
        self.info[i]["Health"] = health
    def get_pos(self, i : int):
        vector = self.info[i]["Pawn"] + self.m_vOldOrigin
        x, y, z = self.pm.read_float(vector), self.pm.read_float(vector + 0x4), self.pm.read_float(vector + 0x8)
        self.info[i]["Pos"] = (x, y, z)

        game_scene = self.pm.read_longlong(self.info[i]["Pawn"] + self.m_pGameSceneNode)
        bone_matrix = self.pm.read_longlong(game_scene + self.m_modelState + 0x80)
        headX = self.pm.read_float(bone_matrix + 6 * 0x20)
        headY = self.pm.read_float(bone_matrix + 6 * 0x20 + 0x4)
        headZ = self.pm.read_float(bone_matrix + 6 * 0x20 + 0x8) + 8
        self.info[i]["HeadPos"] = (headX, headY, headZ)

        legZ = self.pm.read_float(bone_matrix + 28 * 0x20 + 0x8)
        self.info[i]["LegZ"] = legZ
    def get_info(self) -> list:
        self.iterate_entities()
        for i in range(len(self.info)):
            try:
                self.get_TeamNum(i)
                self.get_lifeState(i)
                self.get_Health(i)
                self.get_pos(i)
                
            except Exception as e:
                print(f"Error get_info {i}: {e}")
                continue
        return self.info
    def get_view_info(self) -> tuple:
        pitch = self.pm.read_float(self.dwLocalPlayerPawn + self.m_angEyeAngles)
        yaw = self.pm.read_float(self.dwLocalPlayerPawn + self.m_angEyeAngles + 0x4)
        return (pitch, yaw)
    def get_ViewMatrix(self) -> list:
        view_matrix = [self.pm.read_float(self.client + self.dwViewMatrix + i * 4) for i in range(16)]
        return view_matrix


if __name__ == "__main__":
    c = Cheat()
    c.get_info()
    print(c.info)