import pygame

from src import shared, utils


class Player:
    JUMP_VELOCITY = -150
    MAX_HORIZONTAL_SPEED = 40

    def __init__(self, pos):
        self.collider = utils.Collider(pos, (shared.TILE_SIDE, shared.TILE_SIDE))
        self.gravity = utils.Gravity()

    def update(self):
        dx, dy = 0, 0
        self.gravity.update()

        if shared.kp[pygame.K_SPACE]:
            self.gravity.velocity = Player.JUMP_VELOCITY

        dy += self.gravity.velocity * shared.dt

        dx += shared.keys[pygame.K_d] - shared.keys[pygame.K_a]
        dx *= Player.MAX_HORIZONTAL_SPEED * shared.dt

        collider_data = self.collider.get_collision_data(dx, dy)
        if (
            utils.CollisionSide.BOTTOM in collider_data.colliders
            or utils.CollisionSide.TOP in collider_data.colliders
        ):
            self.gravity.velocity = 0
            dy = 0

        if (
            utils.CollisionSide.RIGHT in collider_data.colliders
            or utils.CollisionSide.LEFT in collider_data.colliders
        ):
            dx = 0

        self.collider.pos += dx, dy
        shared.camera.attach_to(self.collider.pos)

    def draw(self):
        self.collider.draw()
