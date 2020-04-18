import numpy as np
from multiagent.core import World, Agent, Landmark
from multiagent.scenario import BaseScenario


class Scenario(BaseScenario):
    def make_world(self):
        world = World()
        # set any world properties first
        world.dim_c = 2
        num_good_agents = 2
        num_adversaries = 2
        num_agents = num_adversaries + num_good_agents
        num_landmarks = 1
        # add agents
        world.agents = [Agent() for i in range(num_agents)]
        for i, agent in enumerate(world.agents):
            agent.name = 'agent %d' % i
            agent.collide = True
            agent.silent = True
            agent.adversary = True if i < num_adversaries else False
            agent.size = 0.05 if agent.adversary else 0.05
            agent.accel = 3.0 if agent.adversary else 3.0
            # agent.accel = 20.0 if agent.adversary else 25.0
            agent.max_speed = 1.0 if agent.adversary else 1.0
        # add landmarks
        world.landmarks = [Landmark() for i in range(num_landmarks)]
        for i, landmark in enumerate(world.landmarks):
            landmark.name = 'landmark %d' % i
            landmark.collide = True
            landmark.movable = False
            landmark.size = 0.1
            landmark.boundary = False
        # make initial conditions
        self.reset_world(world)
        return world

    def reset_world(self, world):
        # random properties for agents
        for i, agent in enumerate(world.agents):
            agent.color = np.array([0.35, 0.85, 0.35]) if not agent.adversary else np.array([0.85, 0.35, 0.35])
            # random properties for landmarks
        for i, landmark in enumerate(world.landmarks):
            landmark.color = np.array([0.25, 0.25, 0.25])
        # set random initial states
        for agent in world.agents:
            agent.state.p_pos = np.random.uniform(-1, +1, world.dim_p)
            agent.state.p_vel = np.zeros(world.dim_p)
            agent.state.c = np.zeros(world.dim_c)
        for i, landmark in enumerate(world.landmarks):
            if not landmark.boundary:
                landmark.state.p_pos = np.random.uniform(-0.0, +0.0, world.dim_p)
                landmark.state.p_vel = np.zeros(world.dim_p)

    def benchmark_data(self, agent, world):
        # returns data for benchmarking purposes
        if agent.adversary:
            collisions = 0
            for a in self.good_agents(world):
                if self.is_collision(a, agent):
                    collisions += 1
            return collisions
        else:
            return 0

    def is_collision(self, agent1, agent2):
        delta_pos = agent1.state.p_pos - agent2.state.p_pos
        dist = np.sqrt(np.sum(np.square(delta_pos)))
        dist_min = agent1.size + agent2.size + 1
        return True if dist < dist_min else False

    def is_tag(self, agent, world):
        lst_pos = []
        lst_vel = []
        view_distance = 0.2
        for agnt in world.agents:
            if agnt.adversary:
                if (agnt != agent):
                    angle1 = np.arctan2(float(agnt.state.p_pos[0]), float(agnt.state.p_pos[1]))
                    angle2 = np.arctan2(float(agent.state.p_pos[0]), float(agent.state.p_pos[1]))
                    delta_pos = agent.state.p_pos - agnt.state.p_pos
                    # print("in is_tag")
                    if np.sqrt(np.sum(np.square(delta_pos))) <= view_distance + agent.size and abs(
                            angle1 - angle2) <= 0.785398 and (
                            np.sign((agent.state.p_vel[0])) == np.sign((delta_pos[0])) and (
                            np.sign((agent.state.p_vel[1])) == np.sign((delta_pos[1])))):
                        lst_pos.append([agent.state.p_pos[0], agent.state.p_pos[1]])
                        lst_vel.append([agent.state.p_vel[0], agent.state.p_vel[1]])


                    else:
                        continue
        # print("sdfsdfs")
        return lst_pos, lst_vel

    # return all agents that are not adversaries
    def good_agents(self, world):
        return [agent for agent in world.agents if not agent.adversary]

    # return all adversarial agents
    def adversaries(self, world):
        return [agent for agent in world.agents if agent.adversary]

    def reward(self, agent, world):
        # Agents are rewarded based on minimum agent distance to each landmark
        main_reward = self.adversary_reward(agent, world) if agent.adversary else self.agent_reward(agent, world)
        return main_reward

    def agent_reward(self, agent, world):
        # Agents are negatively rewarded if caught by adversaries
        rew = 0
        shape = True
        adversaries = self.adversaries(world)
        if shape:  # reward can optionally be shaped (increased reward for increased distance from adversary)
            a_dist_from_goal = np.sqrt(np.sum(np.square(agent.state.p_pos - world.landmarks[0].state.p_pos)))

            if len(agent.tag_list) > 0:
                for agt in agent.tag_list:
                    dist_from_agnt = np.sqrt(np.sum(np.square(np.asarray(agt) - agent.state.p_pos)))
                    dist_from_goal = np.sqrt(np.sum(np.square(np.asarray(agt) - world.landmarks[0].state.p_pos)))

                    rew += (1 - dist_from_agnt + dist_from_goal) * 10

        if world.goal_flag:
            rew = -100

        if agent.collide:
            for a in adversaries:
                if a.adversary:
                    if self.is_collision(a, agent):
                        rew += 50

        rew -= (1 - a_dist_from_goal) * 10

        return rew

        # agents are penalized for exiting the screen, so that they can be caught by the adversaries

    def bound(x):
        if x < 0.9:
            return 0
        if x < 1.0:
            return (x - 0.9) * 10
        return min(np.exp(2 * x - 2), 10)
        for p in range(world.dim_p):
            x = abs(agent.state.p_pos[p])
            rew -= bound(x)

        return rew

    def adversary_reward(self, adver, world):
        # Adversaries are rewarded for collisions with agents
        rew = 0
        shape = True
        agents = world.agents

        goal_dist = np.sqrt(np.sum(np.square(adver.state.p_pos - world.landmarks[0].state.p_pos)))

        if shape:  # reward can optionally be shaped (increased reward for increased distance from adversary)

            # rew += np.sqrt(np.sum(np.square(agent.state.p_pos - adv.state.p_pos)))
            if len(adver.tag_list) > 0:
                for agt in adver.tag_list:
                    dist = np.sqrt(np.sum(np.square(np.asarray(agt) - adver.state.p_pos)))

                    rew -= 10 * (1 - dist)

        if world.goal_flag:
            rew = 100

        if adver.collide:
            for a in agents:
                if not a.adversary:
                    if self.is_collision(a, adver):
                        rew -= 100

        rew += (1 - goal_dist) * 10

        return rew

    def observation(self, agent, world):
        # get positions of all entities in this agent's reference frame
        agent.tag_list = []

        entity_pos = []
        for entity in world.landmarks:
            if not entity.boundary:
                entity_pos.append(entity.state.p_pos - agent.state.p_pos)
        # communication of all other agents
        comm = []

        other_pos = []
        other_vel = []
        for other in world.agents:
            if other is agent: continue
            comm.append(other.state.c)
            other_pos.append(other.state.p_pos - agent.state.p_pos)
            if not other.adversary:
                other_vel.append(other.state.p_vel)

        tag_pos, tag_vel = self.is_tag(agent, world)
        agent.tag_list = tag_pos

        return np.concatenate([agent.state.p_vel] + [agent.state.p_pos] + entity_pos + other_pos + other_vel)
